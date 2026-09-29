// Reusable carousel function for handling scroll-snap carousels with prev/next buttons

// Pure helpers (no DOM), exported for tests

// Index of the item currently in view, from the scroll position
function carouselIndex(scrollLeft, itemWidth) {
    return Math.round(scrollLeft / itemWidth);
}

// Prev is disabled on the first item, next on the last
function carouselButtonState(index, itemCount) {
    return {
        prevDisabled: index === 0,
        nextDisabled: index === itemCount - 1,
    };
}

// Which dots are active: only the one matching the current item
function carouselDotStates(dotCount, index) {
    return Array.from({ length: dotCount }, (_, i) => i === index);
}

// Index to move to with the next / prev buttons, or null if at the end
function nextCarouselIndex(index, itemCount) {
    return index < itemCount - 1 ? index + 1 : null;
}

function prevCarouselIndex(index) {
    return index > 0 ? index - 1 : null;
}

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
        return carouselIndex(carousel.scrollLeft, getItemWidth());
    }

    // Update active dot and button states based on carousel scroll position
    function updateCarouselState() {
        const currentIndex = getCurrentIndex();
        const buttons = carouselButtonState(currentIndex, items.length);

        // Update dot states if dots exist
        if (dots) {
            const active = carouselDotStates(dots.length, currentIndex);
            dots.forEach((dot, index) => {
                dot.classList.toggle('dot--active', active[index]);
            });
        }

        // Disable/enable prev and next buttons
        prevBtn.disabled = buttons.prevDisabled;
        nextBtn.disabled = buttons.nextDisabled;
    }

    // Scroll to item at given index
    function scrollToItem(index) {
        const itemWidth = getItemWidth();
        const scrollPosition = index * itemWidth;
        carousel.scrollLeft = scrollPosition;
    }

    // Scroll to next item
    function nextItem() {
        const target = nextCarouselIndex(getCurrentIndex(), items.length);
        if (target !== null) {
            scrollToItem(target);
        }
    }

    // Scroll to previous item
    function prevItem() {
        const target = prevCarouselIndex(getCurrentIndex());
        if (target !== null) {
            scrollToItem(target);
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

// Browser only from here: set up the carousels on the page
if (typeof document !== 'undefined') {

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

}

if (typeof module !== "undefined") {
    module.exports = {
        carouselIndex,
        carouselButtonState,
        carouselDotStates,
        nextCarouselIndex,
        prevCarouselIndex,
    };
}
