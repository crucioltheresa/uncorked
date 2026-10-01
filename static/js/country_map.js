// Country Map: Handle country selection via SVG paths with tooltips and keyboard navigation

// Pure helpers (no DOM), exported for tests

// Lookup of ISO code -> country data (name, iso_code, wine_count)
function buildIsoMap(countryData) {
  const isoMap = {};
  countryData.forEach(country => {
    isoMap[country.iso_code] = country;
  });
  return isoMap;
}

// A country on the map is clickable only if we have wines from it
function isCountryClickable(isoCode, isoMap) {
  return Boolean(isoMap[isoCode]);
}

// Screen reader label for a clickable country
function countryAriaLabel(countryInfo) {
  return `${countryInfo.name}: ${countryInfo.wine_count} wines`;
}

// Tooltip wording: "1 wine" / "3 wines"
function wineCountLabel(count) {
  return `${count} wine${count !== 1 ? 's' : ''}`;
}

// Catalogue URL filtered by country
function countryFilterUrl(wineListUrl, countryName) {
  return `${wineListUrl}?country=${encodeURIComponent(countryName)}`;
}

if (typeof document !== 'undefined') (function() {
  const svgPaths = document.querySelectorAll('.world-map__country');
  const countriesDataEl = document.getElementById('countriesData');

  // Exit if data not found (page doesn't have countries data)
  if (!countriesDataEl) return;

  const countryData = JSON.parse(countriesDataEl.textContent);

  // Create lookup map for ISO code -> country data
  const isoMap = buildIsoMap(countryData);

  // Add hover/focus interactions to SVG paths
  svgPaths.forEach(path => {
    const isoCode = path.id;
    const countryInfo = isoMap[isoCode];

    if (isCountryClickable(isoCode, isoMap)) {
      path.classList.add('world-map__country--has-wines');
      path.setAttribute('aria-label', countryAriaLabel(countryInfo));
      path.setAttribute('tabindex', '0');

      // Hover: show tooltip
      path.addEventListener('mouseenter', () => {
        showTooltip(path, countryInfo);
      });

      // Focus: show tooltip
      path.addEventListener('focus', () => {
        showTooltip(path, countryInfo);
      });

      // Leave: hide tooltip
      path.addEventListener('mouseleave', () => {
        hideTooltip();
      });

      // Blur: hide tooltip
      path.addEventListener('blur', () => {
        hideTooltip();
      });

      // Click: navigate to wines filtered by country
      path.addEventListener('click', () => {
        navigateToCountry(countryInfo.name);
      });

      // Enter/Space: navigate to country wines
      path.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          navigateToCountry(countryInfo.name);
        }
      });
    }
  });

  // Tooltip state
  let tooltipEl = null;

  // Show tooltip with country name and wine count
  function showTooltip(pathEl, countryInfo) {
    if (tooltipEl) {
      tooltipEl.remove();
    }

    tooltipEl = document.createElement('div');
    tooltipEl.className = 'world-map-tooltip';
    tooltipEl.innerHTML = `
      <strong>${countryInfo.name}</strong><br>
      ${wineCountLabel(countryInfo.wine_count)}
    `;
    document.body.appendChild(tooltipEl);

    // Position tooltip above path center
    const rect = pathEl.getBoundingClientRect();
    tooltipEl.style.left = (rect.left + rect.width / 2) + 'px';
    tooltipEl.style.top = (rect.top - 40) + 'px';
  }

  // Hide tooltip
  function hideTooltip() {
    if (tooltipEl) {
      tooltipEl.remove();
      tooltipEl = null;
    }
  }

  // Navigate to wines filtered by country. The catalogue URL comes from the
  // map container, so it never picks up a link that already has a query.
  function navigateToCountry(countryName) {
    const container = document.querySelector('[data-wine-list-url]');
    const wineListUrl = container ? container.dataset.wineListUrl : '/wines/';
    window.location.href = countryFilterUrl(wineListUrl, countryName);
  }
})();

if (typeof module !== "undefined") {
  module.exports = {
    buildIsoMap,
    isCountryClickable,
    countryAriaLabel,
    wineCountLabel,
    countryFilterUrl,
  };
}
