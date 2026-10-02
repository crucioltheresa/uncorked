# Lighthouse report

Run on 2 October 2026 with Lighthouse 13.5.0 (`npx lighthouse`, headless Chrome) against the live site. Mobile uses Lighthouse's default mobile emulation and throttling; desktop uses `--preset=desktop`. Scores vary a little between runs. The homepage was re-run after page compression (gzip) and the award logo fix were deployed.

| Page | Device | Performance | Accessibility | Best practices | SEO | Report |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| [Homepage](https://uncorked-store-5dff5e1aa357.herokuapp.com/) | Mobile | 73 | 100 | 100 | 100 | [HTML](lighthouse/homepage-mobile.html) |
| [Homepage](https://uncorked-store-5dff5e1aa357.herokuapp.com/) | Desktop | 88 | 100 | 100 | 100 | [HTML](lighthouse/homepage-desktop.html) |
| [Catalogue](https://uncorked-store-5dff5e1aa357.herokuapp.com/wines/) | Mobile | 83 | 100 | 100 | 100 | [HTML](lighthouse/catalogue-mobile.html) |
| [Catalogue](https://uncorked-store-5dff5e1aa357.herokuapp.com/wines/) | Desktop | 88 | 100 | 100 | 100 | [HTML](lighthouse/catalogue-desktop.html) |
| [Wine page](https://uncorked-store-5dff5e1aa357.herokuapp.com/wines/gulp-hablo-2022/) | Mobile | 86 | 96 | 100 | 100 | [HTML](lighthouse/wine-page-mobile.html) |
| [Wine page](https://uncorked-store-5dff5e1aa357.herokuapp.com/wines/gulp-hablo-2022/) | Desktop | 92 | 96 | 100 | 100 | [HTML](lighthouse/wine-page-desktop.html) |
| [Cart](https://uncorked-store-5dff5e1aa357.herokuapp.com/cart/) | Mobile | 88 | 96 | 100 | 69 | [HTML](lighthouse/cart-mobile.html) |
| [Cart](https://uncorked-store-5dff5e1aa357.herokuapp.com/cart/) | Desktop | 94 | 100 | 100 | 69 | [HTML](lighthouse/cart-desktop.html) |

## Known results

- **Cart SEO 69:** deliberate. The cart is a personal page, so it has `noindex` and Lighthouse reports "Page is blocked from indexing".
- **Accessibility 96 (wine page, cart mobile):** a timing artefact of the promo bar. Its messages fade in and out, and Lighthouse sometimes measures the text mid-fade, when it is almost transparent. At rest the text has full contrast. Users who prefer reduced motion get a still message with no fade (`prefers-reduced-motion` is respected), but Lighthouse doesn't emulate that setting.
- **Homepage mobile performance 73:** the server responds quickly (about 270 ms), pages are sent gzipped and the hero is a 55 KB WebP, so none of these is the bottleneck. The score is limited mainly by:
  - **Render-blocking stylesheets:** Bootstrap, Bootstrap Icons, the Google Fonts CSS and `style.css` must load before the first paint.
  - **New Arrivals card images:** on high-density phone screens the 800px versions (about 125–165 KB each) are picked.
