// Reusable carousel function for handling scroll-snap carousels with prev/next buttons
function initCarousel(carouselSelector, prevBtnSelector, nextBtnSelector, dotsSelector = null) {
    const carousel = document.querySelector(carouselSelector);
    const prevBtn = document.querySelector(prevBtnSelector);
    const nextBtn = document.querySelector(nextBtnSelector);
    const dots = dotsSelector ? document.querySelectorAll(dotsSelector) : null;

    if (!carousel || !prevBtn || !nextBtn) return;

    const items = carousel.children;

    // Calculate item width (item + gap)
    const getItemWidth = () => items[0]?.offsetWidth + 16 || 0; // 16px = var(--space-sm)

    // Get current item index based on scroll position
    function getCurrentIndex() {
        const scrollPosition = carousel.scrollLeft;
        const itemWidth = getItemWidth();
        return Math.round(scrollPosition / itemWidth);
    }

    // Update active dot and button states based on carousel scroll position
    function updateCarouselState() {
        const currentIndex = getCurrentIndex();
        const isFirst = currentIndex === 0;
        const isLast = currentIndex === items.length - 1;

        // Update dot states if dots exist
        if (dots) {
            dots.forEach((dot, index) => {
                dot.classList.toggle('dot--active', index === currentIndex);
            });
        }

        // Disable/enable prev and next buttons
        prevBtn.disabled = isFirst;
        nextBtn.disabled = isLast;
    }

    // Scroll to item at given index
    function scrollToItem(index) {
        const itemWidth = getItemWidth();
        const scrollPosition = index * itemWidth;
        carousel.scrollLeft = scrollPosition;
    }

    // Scroll to next item
    function nextItem() {
        const currentIndex = getCurrentIndex();
        if (currentIndex < items.length - 1) {
            scrollToItem(currentIndex + 1);
        }
    }

    // Scroll to previous item
    function prevItem() {
        const currentIndex = getCurrentIndex();
        if (currentIndex > 0) {
            scrollToItem(currentIndex - 1);
        }
    }

    // Set up dot click listeners
    if (dots) {
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                scrollToItem(index);
            });
        });
    }

    // Set up prev/next button listeners
    prevBtn.addEventListener('click', prevItem);
    nextBtn.addEventListener('click', nextItem);

    // Update carousel state on scroll (debounced)
    let scrollTimeout;
    carousel.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(updateCarouselState, 100);
    });

    // Initialize carousel state on page load
    updateCarouselState();
}

// Initialize reviews carousel
(function() {
    initCarousel(
        '.reviews-carousel',
        '#reviewsPrevBtn',
        '#reviewsNextBtn',
        '.dot'
    );
})();

// Initialize new arrivals carousel on tablet and above
(function() {
    // Only initialize on tablet+ (768px and above)
    const mediaQuery = window.matchMedia('(min-width: 768px)');

    function initNewArrivalsCarousel() {
        if (mediaQuery.matches) {
            initCarousel(
                '.wine-grid.wine-grid--carousel',
                '.wine-carousel-prev',
                '.wine-carousel-next'
            );
        }
    }

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNewArrivalsCarousel);
    } else {
        initNewArrivalsCarousel();
    }

    // Re-initialize on resize
    mediaQuery.addEventListener('change', initNewArrivalsCarousel);
})();
