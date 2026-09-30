// Store Dashboard: on small screens the section menu is a horizontal,
// scrollable tab bar. This scrolls it so the current section is visible
// (centred when possible) instead of hidden off to the side.

/**
 * scrollLeft that centres a tab in the bar, kept within the scroll range.
 * Pure, so it can be tested without a browser.
 * @param {number} tabLeft - tab's offsetLeft inside the bar
 * @param {number} tabWidth
 * @param {number} barWidth - visible width of the bar
 * @param {number} scrollWidth - full scrollable width of the bar
 * @returns {number}
 */
function tabScrollLeft(tabLeft, tabWidth, barWidth, scrollWidth) {
    const centred = tabLeft - (barWidth - tabWidth) / 2;
    const max = Math.max(0, scrollWidth - barWidth);
    return Math.min(Math.max(0, centred), max);
}

if (typeof document !== 'undefined') {
    const bar = document.querySelector('[data-dashboard-tabs]');
    const active = bar && bar.querySelector('[aria-current="page"]');
    // Only needed when the bar actually scrolls (mobile layout)
    if (active && bar.scrollWidth > bar.clientWidth) {
        const item = active.closest('li') || active;
        bar.scrollLeft = tabScrollLeft(
            item.offsetLeft, item.offsetWidth, bar.clientWidth, bar.scrollWidth
        );
    }
}

if (typeof module !== 'undefined') {
    module.exports = { tabScrollLeft };
}
