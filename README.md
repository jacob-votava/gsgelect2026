# GSG Elections 2026

Static site for browsing Graduate Student Government election candidates by position. Built with plain HTML/CSS/JS so it works on GitHub Pages without a build step.

## Repo layout
- `index.html` — single-page experience with tabs for each position.
- `assets/data/candidates.json` — generated data pulled from the provided spreadsheet.
- `assets/headshots/` — extracted headshot images from the spreadsheet.
- `assets/css/` and `assets/js/` — styling and small JS helpers (`home.js` loads/render the data).
- `assets/GSG_election_candidates.xlsx` — authoritative spreadsheet provided by the committee.
- `scripts/extract_candidates.py` — standard-library script that regenerates `candidates.json` and headshots from the spreadsheet.
- `.github/workflows/pages.yml` — GitHub Pages deployment using the same workflow pattern as the prior site.

## Run locally
```bash
# from the repo root
python3 -m http.server 8000
# then open http://localhost:8000
```

## Update the data
1. Replace `assets/GSG_election_candidates.xlsx` with the latest file.
2. Regenerate the JSON + headshots:
   ```bash
   python3 scripts/extract_candidates.py
   ```
3. Reload the page (or redeploy) to see the updates.

## Deploy
Push to `main` and enable GitHub Pages for the repo (source: GitHub Actions). The included workflow uploads the static files and publishes them automatically.
