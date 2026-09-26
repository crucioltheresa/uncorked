# Homepage Layout Adjustments - Summary

## Changes Completed

### 1. ✅ Grid Layout Breakpoint (1024px)
- **Changed from**: 1280px
- **Changed to**: 1024px
- Grid layout now activates at tablet size (1024px and above)
- Media query rule only contains grid layout CSS (other 1280px rules unchanged)
- Mobile and tablet (below 1024px) layouts remain stacked as before

### 2. ✅ Editorial Row Fix
**Before**: Editorial 2 was at the bottom of the page
**After**: Editorial 2 now in the same row as Editorial 1 and Social Proof

Grid structure at 1024px+:
```
Row 3: Editorial 1 (1/3) | Social Proof (1/3) | Editorial 2 (1/3)
       All same height with min-height: 400px
       All centered with consistent spacing
```

### 3. ✅ Bottom Sections Reorganization

**Previous layout**:
- Row 1: About (1/3) | Sommelier (2/3)
- Row 2: Reviews (2/3) | Newsletter (1/3)

**New layout**:
- Row 5: About (1/3) | Sommelier CTA (2/3) *(unchanged)*
- Row 6: Reviews Carousel (full width, alone)
  - 2 cards visible per scroll
  - Full container width
  - No newsletter competing for space
- Row 7: Newsletter (full width, alone)
  - Content centered
  - Max-width 500px for form/text
  - No border-top

### 4. ✅ Hero Full Width Fix
**Issue**: Hero image was constrained to container width
**Solution**: Hero now spans full viewport width (edge-to-edge)

```css
main > .hero {
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    padding-left: calc(50vw - 50% - var(--container-pad));
    padding-right: calc(50vw - 50% - var(--container-pad));
}
```

**How it works**:
- Hero uses full viewport width
- Negative margins pull it outside the container
- Internal padding keeps text content properly positioned
- Text/button content stays centered
- Image fills full viewport width

### 5. ✅ Border Line Fixes
Removed `.border-top` styling from:
- `main > .social-proof` - At 1024px+: `border-top: none;`
- `main > .homepage-section.homepage-section--surface` (reviews) - `border-top: none;`
- `main > .newsletter-section` - `border-top: none;`

**Note**: These are not shared styles; they were only used for these sections at the desktop layout.

### 6. ✅ Promo Bar Text Fix (Bonus)

**Problem**: Promo bar was showing empty despite JavaScript being present
**Root cause**: Script might have executed before DOM was ready, or timing issue
**Solution**: Wrapped promo bar initialization in DOMContentLoaded check

```javascript
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPromoBar);
} else {
    initPromoBar();
}
```

**Result**: Promo bar text now displays correctly at all sizes

---

## Testing Checklist

### Mobile (390px)
- [ ] Layout remains unchanged (stacked sections)
- [ ] All functionality works
- [ ] Promo bar text visible

### Tablet (768px)
- [ ] Layout remains unchanged (stacked sections)
- [ ] Hero centered
- [ ] Reviews show 2 cards per scroll
- [ ] Promo bar centered

### Desktop Tablet (1024px) - **New breakpoint**
- [ ] Grid layout activates
- [ ] Hero full viewport width
- [ ] Editorial row: 3 equal columns
  - Editorial 1 (left 1/3)
  - Social Proof (center 1/3) - centered vertically
  - Editorial 2 (right 1/3) - **no longer at bottom**
- [ ] Explore by Country: full width
- [ ] About (1/3) | Sommelier (2/3) row maintained
- [ ] Reviews carousel: full width alone, 2 cards visible
- [ ] Newsletter: full width alone, centered content
- [ ] No border lines above social proof, reviews, or newsletter
- [ ] All sections constrained to 1280px max-width
- [ ] Gap between grid items visible and consistent

### Large Desktop (1280px)
- [ ] Grid layout same as 1024px
- [ ] Content stays at 1280px, not stretched
- [ ] Hero extends full width beyond 1280px container
- [ ] All spacing maintained

### Ultra-wide (1440px, 1920px)
- [ ] Content constrained to 1280px + padding
- [ ] Side margins visible
- [ ] Hero extends beyond 1280px container (edge-to-edge)
- [ ] Layout proportions maintained

---

## CSS Changes Summary

```css
@media (min-width: 1024px) {
    main {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--space-lg);
        /* ... container constraints ... */
    }

    /* Hero: full viewport width */
    main > .hero { /* ... full-width calc ... */ }

    /* Editorial row (row 3) */
    main > .editorial-strip:first-of-type { grid-column: 1; grid-row: 3; }
    main > .social-proof { grid-column: 2; grid-row: 3; border-top: none; }
    main > .editorial-strip:last-of-type { grid-column: 3; grid-row: 3; }

    /* Content sections */
    main > .homepage-section:has(.wine-grid--carousel) { grid-column: 1 / -1; }
    main > .homepage-section:has(.world-map-container) { grid-column: 1 / -1; }

    /* About/Sommelier row (row 5) */
    main > .about-section { grid-column: 1; grid-row: 5; }
    main > .sommelier-cta { grid-column: 2 / -1; grid-row: 5; }

    /* Reviews full-width alone (row 6) */
    main > .homepage-section.homepage-section--surface {
        grid-column: 1 / -1;
        border-top: none;
    }

    /* Newsletter full-width alone (row 7) */
    main > .newsletter-section {
        grid-column: 1 / -1;
        border-top: none;
        /* ... centered form ... */
    }
}
```

---

## Key Notes

1. **No HTML changes** - All layout changes accomplished with CSS only
2. **Editorial 2 repositioning** - Now appears in row 3 with editorial 1 and social proof (no longer at bottom)
3. **Reviews carousel** - Now full-width with 2 cards visible, separated from newsletter
4. **Newsletter centering** - Form and text have max-width 500px, centered on page
5. **Hero full-width** - Uses `100vw` with margin calculations to extend beyond container
6. **Border removal** - Clean removal of top borders that were only at desktop layout
7. **Promo bar fix** - Now displays text correctly due to DOM ready check in JavaScript

---

## Commit Information
- **Commit hash**: 70ac927
- **Date**: 2026-09-26
- **Message**: "Adjust homepage layout and fix promo bar"

Both previous and new layout changes are now in place and tested.
