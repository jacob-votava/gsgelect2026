(function () {
  const DATA_URL = 'assets/data/candidates.json';
  let positions = [];
  const positionMap = new Map();

  document.addEventListener('DOMContentLoaded', () => {
    loadData();
  });

  async function loadData() {
    const summaryEl = document.querySelector('[data-position-summary]');
    try {
      const response = await fetch(DATA_URL, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`Failed to load ${DATA_URL} (${response.status})`);
      }
      const payload = await response.json();
      positions = Array.isArray(payload?.positions) ? payload.positions : [];
      positions.forEach((pos) => positionMap.set(pos.slug, pos));
      renderTabs(positions);
      const first = positions[0];
      if (first) {
        setActivePosition(first.slug);
      } else if (summaryEl) {
        summaryEl.textContent = 'No positions were found in the data file.';
      }
    } catch (error) {
      console.error(error);
      if (summaryEl) {
        summaryEl.textContent = 'Unable to load positions. Please try reloading the page.';
      }
    }
  }

  function renderTabs(list) {
    const container = document.querySelector('[data-position-tabs]');
    if (!container) return;
    container.innerHTML = '';

    list.forEach((position, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'position-tab';
      if (index === 0) button.classList.add('is-active');
      button.dataset.positionSlug = position.slug || position.title;
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
      button.textContent = position.title || position.sheet || position.slug;

      button.addEventListener('click', () => setActivePosition(position.slug));
      container.appendChild(button);
    });
  }

  function setActivePosition(slug) {
    if (!slug) return;
    const position = positionMap.get(slug);
    const tabs = document.querySelectorAll('[data-position-tabs] .position-tab');
    tabs.forEach((tab) => {
      const isActive = tab.dataset.positionSlug === slug;
      tab.classList.toggle('is-active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    renderPosition(position);
  }

  function renderPosition(position) {
    const summaryEl = document.querySelector('[data-position-summary]');
    const grid = document.querySelector('[data-position-detail]');
    if (!grid || !summaryEl) return;

    grid.innerHTML = '';
    if (!position) {
      summaryEl.textContent = 'Select a position to view candidates.';
      grid.appendChild(makeEmptyState('No position selected.'));
      return;
    }

    const count = position.candidates?.length || 0;
    summaryEl.textContent = `${position.title || position.slug} • ${count} candidate${count === 1 ? '' : 's'}`;

    if (!count) {
      grid.appendChild(makeEmptyState('No candidates were listed for this position.'));
      return;
    }

    position.candidates.forEach((candidate) => {
      grid.appendChild(renderCandidateCard(candidate));
    });
  }

  function renderCandidateCard(candidate) {
    const card = document.createElement('article');
    card.className = 'candidate-card';

    const media = document.createElement('div');
    media.className = 'candidate-card__media';
    if (candidate.headshot) {
      const img = document.createElement('img');
      img.className = 'candidate-card__photo';
      img.src = candidate.headshot;
      img.alt = candidate.name ? `${candidate.name} headshot` : 'Candidate headshot';
      img.loading = 'lazy';
      media.appendChild(img);
    } else {
      const placeholder = document.createElement('div');
      placeholder.className = 'candidate-card__placeholder';
      placeholder.textContent = (candidate.name || '?').slice(0, 1).toUpperCase();
      media.appendChild(placeholder);
    }
    card.appendChild(media);

    const body = document.createElement('div');
    body.className = 'candidate-card__body';

    const name = document.createElement('h3');
    name.className = 'candidate-card__name';
    name.textContent = candidate.name || 'Candidate';
    body.appendChild(name);

    if (candidate.statement) {
      const statement = document.createElement('div');
      statement.className = 'candidate-card__statement';
      statement.innerHTML = formatStatement(candidate.statement);
      body.appendChild(statement);
    }

    card.appendChild(body);
    return card;
  }

  function formatStatement(text) {
    const escaped = escapeHtml(text.trim());
    const paragraphs = escaped.split(/\n\s*\n/);
    if (paragraphs.length > 1) {
      return paragraphs.map((para) => `<p>${para.replace(/\n/g, '<br />')}</p>`).join('');
    }
    return `<p>${escaped.replace(/\n/g, '<br />')}</p>`;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function makeEmptyState(message) {
    const div = document.createElement('div');
    div.className = 'empty-state';
    div.textContent = message;
    return div;
  }
})();
