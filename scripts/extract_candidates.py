#!/usr/bin/env python3
"""
Convert the GSG election spreadsheet into JSON + extracted headshots.

This script only uses the Python standard library so it can run anywhere.
"""
from __future__ import annotations

import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "assets" / "GSG_election_candidates.xlsx"
DATA_PATH = ROOT / "assets" / "data" / "candidates.json"
HEADSHOT_DIR = ROOT / "assets" / "headshots"

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

POSITION_NAME_OVERRIDES = {
    "Vice President of Internal Affa": "Vice President of Internal Affairs",
    "International Student Affairs O": "International Student Affairs Officer",
}


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def load_shared_strings(zip_file: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    return [
        "".join(t.text or "" for t in si.findall(".//main:t", NS))
        for si in root.findall(".//main:si", NS)
    ]


def load_sheet_targets(zip_file: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rel_root = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rel_root.findall("rel:Relationship", NS)
    }

    sheets = []
    for sheet in workbook.find("main:sheets", NS):
        rel_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = rel_map.get(rel_id)
        if not target:
            continue
        sheet_path = posixpath.normpath(posixpath.join("xl", target))
        sheets.append((sheet.attrib.get("name", target), sheet_path))
    return sheets


def read_sheet_rows(zip_file: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> list[tuple[int, dict[str, str]]]:
    root = ET.fromstring(zip_file.read(sheet_path))
    rows: list[tuple[int, dict[str, str]]] = []

    for row in root.findall(".//main:row", NS):
        row_idx = int(row.attrib.get("r", "0"))
        cells: dict[str, str] = {}
        for cell in row.findall("main:c", NS):
            coord = cell.attrib.get("r", "")
            col = "".join(filter(str.isalpha, coord))
            cell_type = cell.attrib.get("t")
            value_element = cell.find("main:v", NS)
            if value_element is None or col == "":
                continue
            raw_value = value_element.text or ""
            if cell_type == "s":
                raw_value = shared_strings[int(raw_value)]
            cells[col] = raw_value
        rows.append((row_idx, cells))
    return rows


def find_drawing_path(zip_file: zipfile.ZipFile, sheet_path: str) -> str | None:
    rel_path = posixpath.join(
        posixpath.dirname(sheet_path),
        "_rels",
        f"{Path(sheet_path).name}.rels",
    )
    if rel_path not in zip_file.namelist():
        return None

    rel_root = ET.fromstring(zip_file.read(rel_path))
    for rel in rel_root.findall("rel:Relationship", NS):
        if rel.attrib.get("Type", "").endswith("/drawing"):
            target = rel.attrib["Target"]
            return posixpath.normpath(posixpath.join(posixpath.dirname(sheet_path), target))
    return None


def map_anchor_rows_to_images(zip_file: zipfile.ZipFile, drawing_path: str) -> dict[int, str]:
    drawing_rel_path = posixpath.join(
        posixpath.dirname(drawing_path),
        "_rels",
        f"{Path(drawing_path).name}.rels",
    )
    rel_root = ET.fromstring(zip_file.read(drawing_rel_path))
    rel_map = {
        rel.attrib["Id"]: posixpath.normpath(posixpath.join(posixpath.dirname(drawing_path), rel.attrib["Target"]))
        for rel in rel_root.findall("rel:Relationship", NS)
    }

    drawing = ET.fromstring(zip_file.read(drawing_path))
    anchors = {}
    for anchor in drawing:
        from_cell = anchor.find("xdr:from", NS)
        pic = anchor.find("xdr:pic", NS)
        if from_cell is None or pic is None:
            continue

        row_idx = int(from_cell.find("xdr:row", NS).text)
        blip = pic.find(".//a:blip", NS)
        if blip is None:
            continue
        embed_id = blip.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
        image_path = rel_map.get(embed_id)
        if not image_path:
            continue
        anchors[row_idx + 1] = image_path  # anchor rows are zero-indexed
    return anchors


def ensure_headshot_path(base: str, ext: str) -> Path:
    return HEADSHOT_DIR / f"{base}{ext}"


def main() -> int:
    if not XLSX_PATH.exists():
        print(f"Missing spreadsheet at {XLSX_PATH}", file=sys.stderr)
        return 1

    HEADSHOT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(XLSX_PATH) as zip_file:
        shared_strings = load_shared_strings(zip_file)
        sheet_targets = load_sheet_targets(zip_file)

        positions = []
        for sheet_name, sheet_path in sheet_targets:
            display_name = POSITION_NAME_OVERRIDES.get(sheet_name, sheet_name)
            drawing_path = find_drawing_path(zip_file, sheet_path)
            row_image_map = map_anchor_rows_to_images(zip_file, drawing_path) if drawing_path else {}

            rows = read_sheet_rows(zip_file, sheet_path, shared_strings)
            if not rows:
                continue
            header_cells = rows[0][1]
            header_map = {col: header_cells[col] for col in header_cells}

            candidates = []
            for row_idx, cells in rows[1:]:
                name = (cells.get("A") or "").strip()
                if not name:
                    continue

                statement = (cells.get("C") or "").replace("\t", " ").strip()
                headshot_rel = row_image_map.get(row_idx)

                headshot_path = None
                if headshot_rel:
                    zip_image_path = posixpath.normpath(headshot_rel)
                    image_bytes = zip_file.read(zip_image_path)
                    ext = Path(zip_image_path).suffix or ".jpg"
                    file_stem = f"{slugify(display_name)}-{slugify(name) or f'row-{row_idx}'}"
                    output_path = ensure_headshot_path(file_stem, ext)
                    if output_path.exists():
                        output_path.unlink()
                    output_path.write_bytes(image_bytes)
                    headshot_path = str(output_path.relative_to(ROOT))

                candidates.append(
                    {
                        "name": name,
                        "statement": statement,
                        "headshot": headshot_path,
                    }
                )

            positions.append(
                {
                    "title": display_name,
                    "slug": slugify(display_name),
                    "sheet": sheet_name,
                    "candidates": candidates,
                }
            )

    DATA_PATH.write_text(json.dumps({"positions": positions}, indent=2), encoding="utf-8")
    print(f"Wrote {DATA_PATH}")
    print(f"Extracted headshots to {HEADSHOT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
