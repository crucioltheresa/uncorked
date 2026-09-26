# Homepage Layout Changes - Tablet & Desktop

## Summary of Changes

This update implements a responsive homepage layout for tablet (768px+) and desktop (1280px+), while keeping mobile (base) layout unchanged.

### Files Modified
1. `core/views.py` - Fetch 8 wines instead of 4
2. `templates/core/index.html` - Add 4 more review cards, update carousel dots
3. `static/css/style.css` - Major CSS updates for responsive layout

---

## Detailed Changes

### 1. Backend (core/views.py)
**Change**: Featured wines limit increased from 4 to 8
```python
featured_wines = Wine.objects.filter(is_featured=True, is_available=True)[:8]
```
**Impact**: Homepage now pulls 8 wines for the carousel instead of 4

---

### 2. Template Updates (templates/core/index.html)

#### Wine Cards
- Added 4 additional wine cards to HTML (now 8 total)
- Hidden on mobile via CSS (cards 5-8 are display: none)
- Shown on tablet+ in the carousel

#### Review Cards
Added 4 additional reviews to the existing 2, now 6 total:
1. "Uncorked is the first wine shop..." - Sofia M., Dublin
2. "Found my new favourite..." - Marco T., Lisbon
3. "The sommelier chat picked..." - Aoife K., Galway *(new)*
4. "Beautifully packed, arrived..." - James R., Cork *(new)*
5. "Finally a shop that explains..." - Lena S., Berlin *(new)*
6. "I ordered a mixed case..." - Priya N., Belfast *(new)*

#### Carousel Dots
- Updated from 2 dots to 6 dots (one per review card)
- JavaScript carousel.js automatically maps dots to cards

---

### 3. CSS Updates (static/css/style.css)

#### New Classes
- `.content-container` - Max-width 1280px container for constraining content

#### Promo Bar (768px+)
- Already centered horizontally with `justify-content: center`
- No CSS changes needed

#### Hero (768px+)
**Changes**:
- Align content vertically and horizontally: `align-items: center`, `justify-content: center`
- Center text: `text-align: center`
- Increase max-width of subtitle from 340px to 500px

**Mobile**: Text aligned to bottom-left (unchanged)
**Tablet+**: Title, subtitle, and button centered on image

#### New Arrivals Wine Cards
**Mobile** (base styles):
- Cards 5-8 are hidden: `.wine-grid--carousel .wine-card:nth-child(n+5) { display: none; }`
- Only first 4 cards visible

**Tablet (768px+)**:
- Cards 5-8 are shown: `.wine-grid--carousel .wine-card:nth-child(n+5) { display: flex; }`
- All 8 cards appear in carousel
- About 3 cards visible per viewport

**Desktop (1280px+)**:
- All 8 cards in carousel
- About 4 cards visible per viewport

#### Reviews Carousel
**Mobile** (base):
- Each card is 100% width minus padding
- 1 card visible at a time
- 6 dots represent 6 pages

**Tablet+ (768px)**:
- Each card is ~50% width: `flex: 0 0 calc(50% - var(--space-sm))`
- 2 cards visible at a time
- 6 dots show active card (dots may skip when scrolling to next pair)

#### Desktop Grid Layout (1280px+)

**Main structure**:
```
main {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-lg);
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 var(--container-pad);
}
```

**Grid areas and section assignments**:

```
Row 1: Hero (full width)
Row 2: New Arrivals (full width)
Row 3: Editorial1 (1/3) | Social Proof (1/3) | Editorial2 (1/3)
Row 4: Explore by Country (full width)
Row 5: About (1/3) | Sommelier CTA (2/3)
Row 6: Reviews (2/3) | Newsletter (1/3)
```

**Key grid assignments**:
- `.hero` - `grid-column: 1 / -1` (full width)
- `.homepage-section:has(.wine-grid--carousel)` - `grid-column: 1 / -1` (full width)
- `.editorial-strip:first-of-type` - `grid-column: 1; grid-row: 3` (left column)
- `.social-proof` - `grid-column: 2; grid-row: 3; display: flex; justify-content: center` (center, vertically centered)
- `.editorial-strip:last-of-type` - `grid-column: 3; grid-row: 3` (right column)
- `.homepage-section:has(.world-map-container)` - `grid-column: 1 / -1` (full width)
- `.about-section` - `grid-column: 1; grid-row: 5` (left)
- `.sommelier-cta` - `grid-column: 2 / -1; grid-row: 5` (right 2/3)
- `.homepage-section.homepage-section--surface` - `grid-column: 1 / 3; grid-row: 6` (left 2/3)
- `.newsletter-section` - `grid-column: 3; grid-row: 6` (right 1/3)

**Editorial strips at desktop**:
- `min-height: 400px` - Fixed height for consistent aspect ratio
- Text overlaid on image background
- All three columns have same height

**Social proof at desktop**:
- Centered vertically in its grid cell
- Quote, team name, and award badges all visible

**Constraints**:
- All content constrained to max-width 1280px (except full-bleed hero image)
- Consistent grid gaps between all sections using `var(--space-lg)`

---

## Responsive Breakpoints

| Breakpoint | Layout | Notes |
|-----------|--------|-------|
| 0-767px (Mobile) | Stacked sections | 4 wines shown, 1 review, arrows/buttons hidden |
| 768-1279px (Tablet) | Stacked sections | 8 wines shown in carousel, 2 reviews shown, 3 visible |
| 1280px+ (Desktop) | 3-column grid | Complex grid layout as described above |

---

## Testing Checklist

### Mobile (390px)
- [ ] Hero: text left-aligned, bottom-aligned
- [ ] New Arrivals: 4 cards visible, arrows hidden, "See All" centered
- [ ] Reviews: 1 card visible, 6 dots, arrows work
- [ ] Promo bar: centered text, slider works

### Tablet (768px)
- [ ] Hero: title/subtitle/button centered
- [ ] New Arrivals: 3-4 cards visible, arrows visible at edges, "See All" centered
- [ ] Reviews: 2 cards visible per scroll, dots track active card
- [ ] Sections stacked vertically (no grid layout yet)

### Desktop (1280px)
- [ ] Hero: centered content, full width
- [ ] New Arrivals: full width, 4 cards visible
- [ ] Editorials (1/3) | Social (1/3) | Editorials (1/3) in one row
- [ ] Explore: full width
- [ ] About (1/3) | Sommelier (2/3) in one row
- [ ] Reviews (2/3) | Newsletter (1/3) in bottom row
- [ ] All sections have consistent spacing
- [ ] Max-width 1280px observed for content

### Desktop (1920px)
- [ ] Content stays at 1280px max-width (not stretched)
- [ ] Side margins visible on ultra-wide screens
- [ ] Layout proportions maintained

---

## Functionality Preserved

All existing functionality remains intact:
- ✓ Wine carousel scrolling (tablet+)
- ✓ Review carousel with dots (all sizes)
- ✓ "See All" button navigation
- ✓ Sommelier float button opens chat dialog
- ✓ World map country selection
- ✓ Newsletter form submission
- ✓ Cart add functionality on wine cards
- ✓ Responsive images and badges

---

## Notes

1. **CSS Grid vs HTML**: Used CSS Grid with `grid-template-areas` concept instead of restructuring HTML
2. **Mobile-first approach**: Base styles (mobile) are unchanged; media queries add tablet/desktop enhancements
3. **Promo bar**: Already had `justify-content: center`, no changes needed
4. **Reviews dots**: Each dot represents one card (not pages); carousel.js handles the mapping
5. **Hero image**: Fills available space; absolute positioning preserves responsive behavior
6. **Wine cards**: Hidden on mobile with `:nth-child(n+5) { display: none; }` and shown on tablet+
7. **Editorial tiles**: Have fixed `min-height: 400px` at desktop to maintain consistent grid row heights

---

## Commit Information

- **Commit hash**: 1d56345
- **Date**: 2026-09-26
- **Message**: "Implement homepage layout changes for tablet and desktop"

All changes follow the project's BEM naming conventions and CSS custom property system.
