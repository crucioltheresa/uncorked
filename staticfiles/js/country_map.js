// Country Map: Handle country selection via SVG paths with tooltips and keyboard navigation
(function() {
  const svgPaths = document.querySelectorAll('.world-map__country');
  const countriesDataEl = document.getElementById('countriesData');

  // Exit if data not found (page doesn't have countries data)
  if (!countriesDataEl) return;

  const countryData = JSON.parse(countriesDataEl.textContent);

  // Create lookup map for ISO code -> country data
  const isoMap = {};
  countryData.forEach(country => {
    isoMap[country.iso_code] = country;
  });

  // Add hover/focus interactions to SVG paths
  svgPaths.forEach(path => {
    const isoCode = path.id;
    const countryInfo = isoMap[isoCode];

    if (countryInfo) {
      path.classList.add('world-map__country--has-wines');
      path.setAttribute('aria-label', `${countryInfo.name}: ${countryInfo.wine_count} wines`);
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
      ${countryInfo.wine_count} wine${countryInfo.wine_count !== 1 ? 's' : ''}
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

  // Navigate to wines filtered by country
  function navigateToCountry(countryName) {
    const wineListUrl = document.querySelector('a[href*="/wines/"]')?.href || '/wines/';
    window.location.href = `${wineListUrl}?country=${encodeURIComponent(countryName)}`;
  }
})();
