(function () {
  document.addEventListener('DOMContentLoaded', initSite);

  function initSite() {
    attachNavToggle();
    updateCurrentYear();
    startCountdown();
  }

  function attachNavToggle() {
    const toggle = document.querySelector('[data-nav-toggle]');
    const panel = document.querySelector('[data-nav-panel]');
    if (!toggle || !panel) return;

    toggle.addEventListener('click', () => {
      const isOpen = panel.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    document.addEventListener('click', (event) => {
      if (!panel.classList.contains('is-open')) return;
      if (event.target === panel || event.target === toggle || panel.contains(event.target)) return;
      panel.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  }

  function updateCurrentYear() {
    const year = new Date().getFullYear();
    const target = document.querySelector('[data-current-year]');
    if (target) {
      target.textContent = year;
    }
  }

  function startCountdown() {
    const daysEl = document.querySelector('[data-count-days]');
    const hoursEl = document.querySelector('[data-count-hours]');
    const minutesEl = document.querySelector('[data-count-minutes]');
    const secondsEl = document.querySelector('[data-count-seconds]');
    if (!daysEl || !hoursEl || !minutesEl || !secondsEl) return;

    const update = () => {
      const now = new Date();
      const target = getNextTargetDate(now);
      const diffMs = Math.max(0, target - now);
      const totalSeconds = Math.floor(diffMs / 1000);

      const days = Math.floor(totalSeconds / (24 * 3600));
      const hours = Math.floor((totalSeconds % (24 * 3600)) / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;

      daysEl.textContent = days.toString();
      hoursEl.textContent = String(hours).padStart(2, '0');
      minutesEl.textContent = String(minutes).padStart(2, '0');
      secondsEl.textContent = String(seconds).padStart(2, '0');
    };

    update();
    setInterval(update, 1000);
  }

  function getNextTargetDate(fromDate) {
    const year = fromDate.getFullYear();
    const targetThisYear = new Date(year, 0, 25, 23, 59, 59, 999); // Jan is month 0
    if (fromDate <= targetThisYear) {
      return targetThisYear;
    }
    return new Date(year + 1, 0, 25, 23, 59, 59, 999);
  }
})();
