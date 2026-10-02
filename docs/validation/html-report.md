# HTML validation report

All pages were checked with the [W3C Nu HTML Checker](https://validator.w3.org/nu/).

| Pages | Checked on | Method | Errors | Warnings |
| --- | --- | --- | ---: | ---: |
| 15 public pages | 2 October 2026 | Live site, by address | 0 | 0 |
| 18 logged-in pages and the 404 page | 2 October 2026 | Local, `python manage.py validate_html` | 0 | 0 |

Total: 34 pages, 0 errors, 0 warnings. One page wasn't checked: the dashboard message detail, because the local database has no contact messages.

## 1. Public pages (live site)

Checked on 2 October 2026. Each live address was entered in the checker (`https://validator.w3.org/nu/?doc=<address>`), and the results page was saved as a screenshot in [screenshots/](screenshots/).

| Page | Address | Errors | Warnings | Screenshot |
| --- | --- | ---: | ---: | --- |
| Homepage | `/` | ✅ 0 | 0 | [html-homepage.png](screenshots/html-homepage.png) |
| Catalogue | `/wines/` | ✅ 0 | 0 | [html-catalogue.png](screenshots/html-catalogue.png) |
| Catalogue: type | `/wines/?type=red` | ✅ 0 | 0 | [html-catalogue-type.png](screenshots/html-catalogue-type.png) |
| Catalogue: country | `/wines/?country=Czech%20Republic` | ✅ 0 | 0 | [html-catalogue-country.png](screenshots/html-catalogue-country.png) |
| Search results | `/wines/?q=red` | ✅ 0 | 0 | [html-search-results.png](screenshots/html-search-results.png) |
| Wine page | `/wines/gulp-hablo-2022/` | ✅ 0 | 0 | [html-wine-page.png](screenshots/html-wine-page.png) |
| Sommelier | `/sommelier/` | ✅ 0 | 0 | [html-sommelier.png](screenshots/html-sommelier.png) |
| About | `/about/` | ✅ 0 | 0 | [html-about.png](screenshots/html-about.png) |
| FAQ | `/faq/` | ✅ 0 | 0 | [html-faq.png](screenshots/html-faq.png) |
| Shipping & Returns | `/shipping-returns/` | ✅ 0 | 0 | [html-shipping-returns.png](screenshots/html-shipping-returns.png) |
| Privacy | `/privacy/` | ✅ 0 | 0 | [html-privacy.png](screenshots/html-privacy.png) |
| Contact | `/contact/` | ✅ 0 | 0 | [html-contact.png](screenshots/html-contact.png) |
| Login | `/accounts/login/` | ✅ 0 | 0 | [html-login.png](screenshots/html-login.png) |
| Signup | `/accounts/signup/` | ✅ 0 | 0 | [html-signup.png](screenshots/html-signup.png) |
| Password reset | `/accounts/password/reset/` | ✅ 0 | 0 | [html-password-reset.png](screenshots/html-password-reset.png) |

## 2. Logged-in pages and the 404 page (local)

Checked on 2 October 2026 with `python manage.py validate_html --customer <email> --manager <email>`. The command renders each page with Django's test client against the local database (logged in as a customer or a store manager, with a bottle in the cart) and sends the HTML to the checker's API. These pages can't be checked by address: the checker would see the login page instead, and the 404 page answers with a 404 status.

They were validated locally with the same templates that are deployed: no template has changed since this run.

| Group | Page | Address | Errors | Warnings |
| --- | --- | --- | ---: | ---: |
| Public | 404 | `/this-page-does-not-exist/` | ✅ 0 | 0 |
| Customer | Wine page (logged in) | `/wines/gulp-hablo-2022/` | ✅ 0 | 0 |
| Customer | Cart with items | `/cart/` | ✅ 0 | 0 |
| Customer | Checkout | `/checkout/` | ✅ 0 | 0 |
| Customer | Profile | `/accounts/profile/` | ✅ 0 | 0 |
| Customer | Order detail | `/order/<order number>/` | ✅ 0 | 0 |
| Customer | Favourites | `/wishlist/` | ✅ 0 | 0 |
| Customer | Order success | `/order/success/<order number>/` | ✅ 0 | 0 |
| Manager | Dashboard overview | `/dashboard/` | ✅ 0 | 0 |
| Manager | Dashboard wines | `/dashboard/wines/` | ✅ 0 | 0 |
| Manager | Dashboard orders | `/dashboard/orders/` | ✅ 0 | 0 |
| Manager | Dashboard order detail | `/dashboard/orders/<order number>/` | ✅ 0 | 0 |
| Manager | Dashboard messages | `/dashboard/messages/` | ✅ 0 | 0 |
| Manager | Dashboard reviews | `/dashboard/reviews/` | ✅ 0 | 0 |
| Manager | Dashboard regions | `/dashboard/regions/` | ✅ 0 | 0 |
| Manager | Add region | `/dashboard/regions/add/` | ✅ 0 | 0 |
| Manager | Add wine | `/wines/add/` | ✅ 0 | 0 |
| Manager | Edit wine | `/wines/gulp-hablo-2022/edit/` | ✅ 0 | 0 |
| Manager | Delete wine (confirmation) | `/wines/gulp-hablo-2022/delete/` | ✅ 0 | 0 |
| Manager | Dashboard message detail | `/dashboard/messages/<id>/` | skipped | no contact messages in the local database |
