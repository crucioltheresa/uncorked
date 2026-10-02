# Uncorked

**Live site:** [https://uncorked-store-5dff5e1aa357.herokuapp.com/](https://uncorked-store-5dff5e1aa357.herokuapp.com/)

Uncorked is an online wine shop I built for a small, independent wine store in Dublin. It sells natural, classic and "everything in between" wines from independent producers across 18 countries, and delivers them across Ireland. Customers can browse by type or by country on a world map, ask a virtual sommelier for a recommendation, save favourites, pay securely with Stripe and review the wines they've bought. The shop owner runs the store from a Store Dashboard without needing the Django admin.

![Uncorked homepage on desktop, tablet and phone](docs/images/responsive.jpg)

---

## Contents

1. [User experience](#user-experience)
2. [Business model](#business-model)
3. [Agile development](#agile-development)
4. [Design](#design)
5. [Features](#features)
6. [Data model](#data-model)
7. [Security and roles](#security-and-roles)
8. [Technologies](#technologies)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Credits](#credits)

---

## User experience

### Purpose

I wanted Uncorked to feel like walking into a good local wine shop: a curated selection rather than a warehouse, honest descriptions of how each wine tastes, and help choosing when you're not sure. The site has to make buying wine simple and trustworthy (clear prices, delivery costs and age rules) on any device.

### Target users

- **Curious wine drinkers in Ireland** who want something more interesting than the supermarket shelf, especially natural and low-intervention wines.
- **People who aren't wine experts** and want guidance in plain language (the sommelier chat, the "character" line on every wine).
- **Customers buying for an occasion or a gift** who want a recommendation and reliable delivery.
- **Returning customers** who want to reorder favourites, see their order history and share reviews.
- **The shop owner and staff**, who need to manage wines, stock, orders, messages and reviews.

All customers must be 18 or over to buy alcohol; the footer and the FAQ say so.

### User goals

- Find wines by type, country, producer, region or name.
- Understand a wine before buying: character, tasting notes, food pairing, price and stock.
- Get a recommendation quickly when unsure.
- Know the full price (bulk discount and delivery) before paying.
- Check out quickly, with or without an account.
- Save favourite wines, see past orders and review wines they've bought.
- Get in touch with the shop easily.

### Site owner goals

- Sell wine online across Ireland.
- Encourage bigger orders with the 8-bottle discount and the free-delivery threshold.
- Build trust with verified-purchase reviews and clear policies.
- Grow an audience through the newsletter, Facebook and search engines.
- Run the shop day to day (stock, orders, messages, reviews) from one dashboard.

---

## Business model

### B2C e-commerce

Uncorked is a **business-to-consumer** (B2C) online shop: it sells bottles directly to individual customers, who pay online by card (Stripe) and receive their wines by delivery. There are no subscriptions or marketplaces; the shop buys from producers and sells to the public.

### Value proposition

- A **curated** selection of wines from independent producers and iconic estates in 18 countries, not an endless catalogue.
- **Plain-language guidance**: every wine has a short "character" description, tasting notes and a food match, and a sommelier chat recommends wines from five quick questions.
- **Transparent pricing**: the bulk discount and the delivery cost are shown before payment.
- **Trustworthy reviews**: only one review per customer per wine, marked "verified purchase" when they bought it.

### Revenue

All pricing rules live in one module (`orders/pricing.py`), so the cart, the checkout and the Stripe payment always agree:

| Rule | Value |
| --- | --- |
| Wine sales | Each wine has its own price; prices are fixed in the cart when a wine is added and saved on the order line at purchase |
| Bulk discount | 10% off when the order has 8 bottles or more |
| Delivery (Ireland only, priced by Eircode) | €5.95 for Dublin Eircodes (routing key starting with D), €9.95 for the rest of Ireland |
| Free delivery | On orders of €100 or more (after the bulk discount) |

Delivery is calculated from the customer's **Eircode**, which is validated (routing key plus four characters) before the order is created.

### Marketing strategy

#### Facebook Business Page

I designed a Facebook Business Page for Uncorked in Figma. It uses the shop's logo, a cover photo with the same "Wine with a point of view." headline as the website, an intro with the website link, delivery and discount details, and example posts announcing new arrivals, the bulk discount and the sommelier chat. The site's footer links to Facebook (opening in a new tab).

<details>
<summary>Facebook Business Page mockup</summary>

![Facebook Business Page mockup for Uncorked](docs/images/facebook-mockup.png)

</details>

#### Newsletter

The homepage and wine pages have a newsletter signup form. Addresses are saved as `NewsletterSubscriber` records (a repeated address just shows a friendly message), ready to be used for new arrivals and offers.

#### SEO

- **Keywords**: page titles and meta descriptions use the phrases customers search for, for example "Natural & Classic Wines from Dublin", "curated wines from independent producers", "delivered across Ireland", and each wine's name, producer and region.
- **Meta tags**: every page has its own `<title>` and meta description, a canonical URL, and Open Graph and Twitter Card tags for link previews (wine pages use the wine's own image).
- **Sitemap**: `/sitemap.xml` lists the homepage, the catalogue, the information pages and every available wine.
- **robots.txt**: `/robots.txt` keeps private pages (accounts, cart, checkout, orders, favourites, dashboard, wine management and the Stripe webhook) out of search engines and points to the sitemap.
- **Semantic, valid HTML** with descriptive link text, image alt text and a logical heading order.

---

## Agile development

I planned and tracked the project with a **GitHub Projects** board: [Uncorked – Development Board](https://github.com/users/crucioltheresa/projects/12).

- Each feature is a **user story** issue ("As a … I want to … So that …") with acceptance criteria and tasks as checklists.
- Stories are grouped into **epics** with labels: `epic: auth`, `epic: products`, `epic: cart`, `epic: orders`, `epic: wishlist`, `epic: reviews`, `epic: sommelier`, `epic: seo`, `epic: ux`.
- Each story has a **MoSCoW** priority label: `must have`, `should have`, `could have` or `wont have`.
- The board columns are Backlog, This Sprint, In Progress and Done. A story moved to Done and was closed only when every acceptance criterion and task was ticked.

### User stories

| Story | Title | Epic | Priority | Status |
| --- | --- | --- | --- | --- |
| US-01 | User Registration | auth | Must have | Done |
| US-02 | User Login and Logout | auth | Must have | Done |
| US-03 | User Profile and Order History | auth | Must have | Done |
| US-04 | Admin Panel Access | auth | Must have | Done |
| US-05 | Browse Wine Catalogue | products | Must have | Done |
| US-06 | Filter Wines by Type | products | Must have | Done |
| US-07 | View Wine Detail Page | products | Must have | Done |
| US-08 | Search Wines | products | Should have | Done |
| US-09 | Admin Manages Wine Catalogue | products | Must have | Done |
| US-10 | Add Wine to Cart | cart | Must have | Done |
| US-11 | View and Manage Cart | cart | Must have | Done |
| US-12 | Complete Checkout | orders | Must have | Done |
| US-13 | Payment Confirmation | orders | Must have | Done |
| US-14 | Payment Failure Feedback | orders | Must have | Done |
| US-15 | Admin Views and Manages Orders | orders | Must have | Done |
| US-16 | Add Wine to Wishlist | wishlist | Must have | Done |
| US-17 | View and Manage Wishlist | wishlist | Must have | Done |
| US-18 | Write a Review | reviews | Must have | Done |
| US-19 | Delete Own Review | reviews | Should have | Done |
| US-20 | Take Wine Quiz | sommelier | Should have | Done |
| US-21 | View Quiz Recommendations | sommelier | Should have | Done |
| US-22 | SEO Implementation | seo | Must have | Done |
| US-23 | Newsletter Signup | seo | Must have | Done |
| US-24 | Facebook Business Page | seo | Must have | Done |
| US-25 | E-commerce Business Model Documentation | seo | Must have | Done |
| US-26 | Homepage | ux | Must have | Done |
| US-27 | Static Pages | ux | Must have | Done |
| US-28 | Responsive Design | ux | Must have | Done |
| US-29 | Explore Wines by Country | products | Should have | Done |
| US-30 | Order Confirmation Email | orders | Must have | Done |
| US-36 | Sign in with Google / Facebook / Apple | auth | Won't have | Backlog |

### Won't have (future work)

**US-36 – Sign in with Google / Facebook / Apple.** Social login would save customers another password. It was deliberately left out of this release (MoSCoW "won't have") and stays in the Backlog as future work.

---

## Design

### Colours

The palette is warm and calm, like a wine shop at night: off-white walls, near-black shelves and a burnt-orange accent. All colours are CSS custom properties in `static/css/style.css`.

| Token | Value | Used for |
| --- | --- | --- |
| `--color-bg` | `#F7F2EC` | Page background |
| `--color-dark` | `#1C1612` | Text, buttons, header bar, footer |
| `--color-accent` | `#B85C2A` | Brand accent: logo shadow, highlights, icons |
| `--color-accent-text` | `#A45225` | Accent text and accent buttons on light backgrounds (4.5:1 contrast) |
| `--color-accent-on-dark` | `#CA652E` | Accent text on the dark footer and photos |
| `--color-mid` | `#9B8B7A` | Borders, icons, muted text on dark backgrounds |
| `--color-mid-text` | `#746658` | Muted text on light backgrounds (4.5:1 contrast) |
| `--color-beige` | `#C9B99A` | Details |
| `--color-surface` | `#F0EAE0` | Alternate section background |
| `--color-border` | `#D9D0C4` | Lines and outlines |
| `--color-card` | `#FFFFFF` | Cards and forms |
| `--color-green` / `--color-error` | `#2E7D32` / `#B71C1C` | Success and error messages, discount |

Each wine type also has a badge colour pair (for example rosé `#FCE4EC` / `#880E4F`).

### Typography

- **Plaster** (Google Fonts) for the bold "Uncorked" logo.
- **Playfair Display** (serif, with italics) for headings, the hero headline and prices.
- **DM Sans** for body text, navigation and buttons.

Fonts load with `font-display: swap`, and the font servers are preconnected.

### Imagery

Real photographs of bottles and wine shop shelves set the mood: a full-width hero, editorial strips with a short message, and a sommelier section. Every wine has a product photo stored on Cloudinary. Icons come from Bootstrap Icons. Homepage photos are served as WebP with a JPEG fallback; wine photos are resized and converted automatically by Cloudinary.

### Wireframes and mockups

I designed the wireframes, the high-fidelity mockups and the Facebook page mockup in Figma: [Uncorked on Figma](https://www.figma.com/design/mnswxvlirwrek7YlplbpXQ/Uncorked---projeto-5?node-id=0-1&t=d3YyChSpnQzkYVJS-1).

### Design changes during development

- **Desktop grid layout**: on large screens the homepage became a grid (new arrivals, editorial strips, social proof, map and reviews side by side) instead of one long column. At first the grid applied to every page; it is now limited to the homepage.
- **Map moved to the homepage**: the "Explore by Country" world map started as its own page and moved onto the homepage, with a Country dropdown in the navigation for quick access.
- **Sommelier as a chat widget**: the wine quiz became a floating chat button available on every page, with the full-page version still at `/sommelier/`.
- **Login pop-up**: logging in and signing up open in a pop-up (Bootstrap modal) instead of leaving the page; the full pages still work without JavaScript.

---

## Features

### Navigation and promo bar

The header has a search box, the logo, favourites, account and cart icons, the wine type categories and a Country dropdown. Below it, a promo bar announces the bulk discount and free delivery (it rotates between messages, and stays still for people who prefer reduced motion). On phones the categories collapse behind a menu button.

![Navigation and promo bar](docs/images/nav-promo.jpg)

<details>
<summary>Mobile menu</summary>

![Mobile navigation menu](docs/images/nav-mobile.jpg)

</details>

### Homepage

A full-width hero ("Wine with a point of view."), a New Arrivals carousel, editorial strips, the shop's philosophy and awards, the world map, an About section, a sommelier call to action, customer reviews and the newsletter signup.

![Homepage](docs/images/homepage.jpg)

### Explore by Country: world map and Country dropdown

An interactive world map highlights the countries Uncorked has wines from. Hovering or focusing a country shows how many wines there are; clicking it (or pressing Enter) opens the catalogue filtered by that country. The same countries are listed in the Country dropdown in the navigation.

![World map](docs/images/map.jpg)

![Country dropdown](docs/images/country-dropdown.jpg)

### Catalogue

All available wines, 12 per page, filtered by type or country from the navigation. Each card shows the photo, a type badge, name, price, region and vintage, the character line, a favourite star and a quantity stepper with Add to Cart.

![Catalogue](docs/images/catalogue.jpg)

### Search

Search looks through wine names, producers, regions and countries and shows how many results were found.

![Search results](docs/images/search.jpg)

### Wine page

Photo, name and vintage, price, stock status, quantity and Add to Cart, the favourites button, and details: country and region, character, tasting notes, food match and, when there is one, a longer description. Reviews are listed with their rating, title and "verified purchase" badge, and "You may also like" shows up to four other wines of the same type.

![Wine page](docs/images/wine-page.jpg)

### Favourites

Logged-in customers can star wines on any card or on the wine page (the star updates without reloading the page). The favourites page lists them with Add to Cart and Remove. Visitors who aren't logged in are asked to log in first.

![Favourites](docs/images/favourites.jpg)

### Cart and cart preview

The cart lists each wine with its thumbnail, price, quantity stepper, line total and Remove. Changing a quantity updates the cart automatically (no reload), including the totals, the discount and the cart badge; without JavaScript an Update button does the same. Quantities are capped at the stock. Hovering the cart icon shows a preview of the cart, and the badge counts bottles, not different wines.

![Cart](docs/images/cart.jpg)

![Cart preview](docs/images/cart-preview.jpg)

### Checkout: Eircode delivery and bulk discount

Customers can check out with or without an account. Logged-in customers' delivery details are filled in from their profile, and they can save new ones to it. The Eircode is validated, delivery is Ireland only, and the order summary shows the subtotal, the 10% discount for 8+ bottles, the delivery cost and the total.

![Checkout](docs/images/checkout.jpg)

### Stripe payment

The payment page shows the final breakdown, with delivery priced from the Eircode, and a Stripe card field. Totals are always calculated on the server from the cart, never from values sent by the browser. When Stripe confirms the payment (webhook), the order is marked Paid and the stock is reduced. If a payment fails, the customer sees Stripe's message and the order stays pending.

![Payment page with discount and Dublin delivery](docs/images/payment.jpg)

### Emails

- **Order confirmation**, sent once when the payment succeeds, with the items, totals and delivery address.
- **Account emails**: email confirmation on signup (required before the first login), password reset, and a "you already have an account" email if someone signs up with an existing address (no second account is created).
- **Contact form**: a confirmation to the customer and a notification to the shop.

![Order confirmation email](docs/images/order-email.jpg)

### Profile and My Reviews

The profile has the customer's delivery details (with Eircode validation), their order history with statuses, and "My Reviews", where they can edit or delete their reviews in a pop-up.

![Profile](docs/images/profile.jpg)

### Reviews from orders

On a paid, shipped or delivered order, each wine has a "Write a review" button (or "Edit your review" if they've already reviewed it). The review opens in a pop-up. Reviews bought this way are marked "verified purchase", and reviewers are shown by name, never by email.

![Order page with review buttons](docs/images/order-reviews.jpg)

### Sommelier chat

A floating chat button opens the virtual sommelier on every page. It asks five questions (type, occasion, food, style and budget) and recommends three wines that match, each with Add to Cart.

![Sommelier chat](docs/images/sommelier-chat.jpg)

### Login and signup pop-up

The account icon opens a pop-up to log in or sign up without leaving the page. After signing up, customers are asked to confirm their email.

![Login pop-up](docs/images/login-modal.jpg)

### Contact and information pages

A contact form (name, email, topic and message, all validated) saves messages for the shop and sends the two emails above. About, FAQ, Shipping & Returns (with the delivery rates and discount taken from the pricing rules) and Privacy pages are linked from the footer, together with Facebook.

![Contact page](docs/images/contact.jpg)

![FAQ](docs/images/faq.jpg)

### 404 and 403 pages

Custom error pages in the site's style ("This bottle's gone missing"), with links back to the shop.

![404 page](docs/images/not-found.jpg)

### Store Dashboard

A dashboard for running the shop, separate from the Django admin:

- **Overview**: paid orders and revenue (last 30 days and all time), orders waiting to be shipped, low stock (5 bottles or fewer), out of stock, unhandled messages and the newest reviews.
- **Wines**: search, filter by type, availability and stock, make a wine available or unavailable, edit or delete.
- **Orders**: search by email, name or order number, filter by status, open an order and change its status (for example to Shipped or Delivered).
- **Messages**: read contact messages, reply by email and mark them as handled.
- **Reviews**: read and delete reviews.
- **Regions**: add and edit wine regions.

![Store Dashboard overview](docs/images/dashboard.jpg)

![Dashboard orders](docs/images/dashboard-orders.jpg)

![Dashboard wines](docs/images/dashboard-wines.jpg)

### Store Manager role

Shop staff don't need to be superusers. A **Store Manager** group (created by a migration) has one permission, "Can use the Store Dashboard". Store Managers get the dashboard and product management, and their account icon leads to the dashboard instead of a customer profile (they have no favourites). The developer account stays a separate superuser with access to the Django admin.

### Product management

Store Managers and superusers can add, edit and delete wines from the front end, including uploading the photo (stored on Cloudinary). Edit and Delete buttons appear on the wine page. A wine that is part of existing orders is never deleted: it is marked unavailable instead, so order history stays intact.

![Wine page for a Store Manager](docs/images/manager-wine-page.jpg)

![Add wine form](docs/images/wine-form.jpg)

### Accessibility

Semantic landmarks and heading order, labelled form fields, focus styles, text alternatives for images and icons, status messages announced to screen readers, 44px touch targets, WCAG AA colour contrast, keyboard access to the map, menus and pop-ups, and respect for `prefers-reduced-motion`.

### Future features

- Sign in with Google, Facebook and Apple (US-36).
- Back-in-stock email alerts.
- Wine subscription boxes.
- Gift cards and gift messages.
- More languages.
- A live Facebook Business Page to replace the mockup, with the footer link pointing to it.

---

## Data model

The cart is stored in the session (wine ID, quantity and price as text), so it needs no table.

```mermaid
erDiagram
    CustomUser ||--|| UserProfile : has
    CustomUser ||--o{ Order : places
    CustomUser ||--o{ Review : writes
    CustomUser ||--o{ WishlistItem : saves
    Region ||--o{ Wine : contains
    Wine ||--o{ OrderItem : "sold as"
    Wine ||--o{ Review : receives
    Wine ||--o{ WishlistItem : "saved as"
    Order ||--|{ OrderItem : contains

    CustomUser {
        int id PK
        string email UK
        string username
        string first_name
        string last_name
    }
    UserProfile {
        int id PK
        int user_id FK
        string full_name
        string email
        string address_line1
        string address_line2
        string city
        string postcode
        string country
    }
    Region {
        int id PK
        string name
        string country
        string slug UK
        text description
    }
    Wine {
        int id PK
        string name
        string producer
        int region_id FK
        string wine_type
        int vintage
        decimal abv
        decimal price
        int stock
        text character
        text tasting_notes
        text food_pairing
        text description
        image image
        string slug UK
        bool is_featured
        bool is_available
    }
    Order {
        int id PK
        uuid order_number UK
        int user_id FK "null for guests"
        string stripe_payment_intent
        string status
        string full_name
        string email
        string address_line1
        string address_line2
        string city
        string postcode
        string country
        decimal subtotal
        decimal discount
        decimal delivery_cost
        decimal grand_total
    }
    OrderItem {
        int id PK
        int order_id FK
        int wine_id FK
        int quantity
        decimal price_at_purchase
    }
    Review {
        int id PK
        int wine_id FK
        int user_id FK
        int rating
        string title
        text body
        bool verified_purchase
    }
    WishlistItem {
        int id PK
        int user_id FK
        int wine_id FK
    }
    NewsletterSubscriber {
        int id PK
        string email UK
        bool active
    }
    ContactMessage {
        int id PK
        string name
        string email
        string subject
        text message
        bool handled
    }
```

| Model | App | Description |
| --- | --- | --- |
| `CustomUser` | accounts | The user, logging in with a unique email instead of a username. Shown publicly by name only. |
| `UserProfile` | accounts | One per user, created automatically: saved delivery details used to fill in the checkout. |
| `Region` | products | A wine region and its country (used by the filters, the map and the Country dropdown). |
| `Wine` | products | A wine with its type, price, stock, descriptions and photo. Unavailable wines are hidden from the shop. |
| `Order` | orders | An order with a random UUID order number, the delivery details, the totals breakdown and a status (pending, paid, shipped, delivered, cancelled). Guests' orders have no user. |
| `OrderItem` | orders | A line of an order, keeping the price paid even if the wine's price changes later. A wine with order lines can't be deleted. |
| `Review` | reviews | A 1–5 star review; one per user per wine, marked as a verified purchase when the user bought it. |
| `WishlistItem` | wishlist | A favourite wine; one per user per wine. |
| `NewsletterSubscriber` | core | A newsletter email address (unique). |
| `ContactMessage` | core | A message from the contact form, which staff can mark as handled. |
| `DashboardAccess` | dashboard | No table: it only holds the "Can use the Store Dashboard" permission given to the Store Manager group. |

---

## Security and roles

- **CSRF protection** on every form, including the ones sent with JavaScript (fetch sends the token).
- **POST-only actions**: adding to and changing the cart, favourites, reviews, order status changes, and deleting wines and reviews all refuse GET requests, and logging out only happens on POST.
- **Order privacy**: order numbers are random UUIDs, not sequential IDs. Logged-in customers can only open their own orders; a guest can only see the success page for the order stored in their own session.
- **Server-side totals**: prices, the discount and delivery are always recalculated on the server; the Stripe amount comes from the order, never from the browser.
- **Stripe webhook**: the signature is checked with the webhook secret before an order is marked paid.
- **Email verification**: new accounts must confirm their email before logging in, and signing up with an existing email never creates a second account.
- **Reviewer privacy**: reviews show the reviewer's name (or the part of their email before the @), never their email address.
- **Roles**: customers; Store Managers (dashboard and product management, through a permission, not superuser status); and the superuser (developer) who also has the Django admin. Store pages check the permission and send everyone else away with a message.
- **Secrets in environment variables**: the secret key, database URL, Stripe keys, Cloudinary URL and email password are read from environment variables (a `.env` file locally, config vars on Heroku) and never committed. `DEBUG` is off in production.
- **Private pages** are excluded from search engines in `robots.txt`.

### Security settings (HTTPS)

In production only (`DEBUG` off and not while the tests run), the site forces HTTPS. Local development and the test suite keep plain HTTP.

| Setting | Value | Why |
| --- | --- | --- |
| `SECURE_PROXY_SSL_HEADER` | `("HTTP_X_FORWARDED_PROTO", "https")` | Heroku ends HTTPS before Django; this header tells Django the request was secure, so the redirect doesn't loop |
| `SECURE_SSL_REDIRECT` | `True` | Sends every HTTP request to HTTPS |
| `SESSION_COOKIE_SECURE` | `True` | The login session cookie is only sent over HTTPS |
| `CSRF_COOKIE_SECURE` | `True` | The CSRF cookie is only sent over HTTPS |
| `SECURE_HSTS_SECONDS` | `3600` | Browsers use HTTPS for this site for an hour |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `False` | The site lives on a Heroku subdomain it doesn't control the rest of |
| `SECURE_HSTS_PRELOAD` | `False` | Not submitted to the browsers' HSTS preload list |

---

## Technologies

### Languages

HTML, CSS, JavaScript and Python.

### Frameworks and libraries

- [Django](https://www.djangoproject.com/) 6.1
- [django-allauth](https://allauth.org/) (accounts, email verification, password reset)
- [Stripe](https://stripe.com/) Python library and Stripe.js (payments)
- [Cloudinary](https://cloudinary.com/) Python SDK (media storage, through a custom Django storage)
- [WhiteNoise](https://whitenoise.readthedocs.io/) (compressed, cached static files)
- [Gunicorn](https://gunicorn.org/) (web server on Heroku)
- [dj-database-url](https://github.com/jazzband/dj-database-url), psycopg2-binary, python-dotenv, Pillow, requests
- [Bootstrap 5.3](https://getbootstrap.com/) (pop-ups and base styles) and [Bootstrap Icons](https://icons.getbootstrap.com/)
- [Google Fonts](https://fonts.google.com/): Plaster, Playfair Display and DM Sans
- [Simple Icons](https://simpleicons.org/) for the payment logos in the footer

### Services

- **Heroku**: hosting
- **Neon**: PostgreSQL database
- **Cloudinary**: wine images
- **Stripe**: card payments (with a webhook)
- **Gmail SMTP**: sending emails

### Tools

Git and GitHub (with GitHub Projects), VS Code, Figma, Chrome DevTools and Lighthouse, Jest, JSHint, flake8, the W3C HTML and CSS validators, and the Heroku CLI.

---

## Testing

### Automated tests

| Suite | Tests | Command |
| --- | ---: | --- |
| Django (Python) | 352 | `python manage.py test` |
| Jest (JavaScript) | 66 | `npm test` |
| flake8 (PEP 8) | 0 issues | `flake8` |
| JSHint | 0 issues | `npm run lint:js` |

The Django tests live in each app's `tests.py` and the Jest tests in `js_tests/`. Every test's docstring (or each Jest file's header) starts with the user story it covers. To run them locally, install the Python requirements and `npm install`, then use the commands above. `flake8` uses the project's `.flake8` file, which leaves out the virtual environment, `node_modules` and migrations.

### User stories and tests

Some tests cover two stories, so they're counted under both.

| Story | Django tests | Jest tests | Main test classes / files |
| --- | ---: | ---: | --- |
| US-01 Registration | 15 | 5 | RegistrationTests, SignupConfirmationEmailTests, AuthModalTests; auth_modal.test.js |
| US-02 Login and logout | 20 | 5 | LoginLogoutTests, EmailVerificationTests, PasswordResetEmailTests, AuthModalTests; auth_modal.test.js |
| US-03 Profile and orders | 25 | 7 | ProfileViewTests, ProfileEircodeTests, ProfileReviewsTests, OrderDetailViewTests; reviews_modal.test.js |
| US-04 Admin access | 14 | 0 | AdminPanelTests, StoreManagerRoleTests, AccountAreaByRoleTests |
| US-05 Catalogue | 7 | 0 | CatalogueTests, CatalogueAccessibilityTests, OptimisedImageTests |
| US-06 Filter by type | 2 | 0 | FilterByTypeTests |
| US-07 Wine page | 7 | 0 | WineDetailTests, RelatedWinesTests, OptimisedImageTests |
| US-08 Search | 6 | 0 | WineSearchTests |
| US-09 Manage wines | 36 | 4 | ProductManagementTests, WinesSectionTests, WineImageUploadTests, DashboardAccessTests; dashboard.test.js |
| US-10 Add to cart | 9 | 0 | AddToCartTests |
| US-11 Cart | 32 | 12 | UpdateCartQuantityTests, CartPreviewTests, CartBadgeTests, ViewManageCartTests; cart.test.js, cart_preview.test.js |
| US-12 Checkout | 24 | 4 | CheckoutTests, CheckoutSubmitTests, EircodeValidationTests, DeliveryCostTests, BulkDiscountTests, GuestCheckoutTests; checkout.test.js |
| US-13 Payment confirmation | 13 | 4 | StripeWebhookTests, CheckoutToWebhookTests, GuestOrderAccessTests, CheckoutSubmitTests; checkout.test.js |
| US-14 Payment failure | 2 | 4 | PaymentFailureTests; checkout.test.js |
| US-15 Manage orders | 12 | 4 | OrdersSectionTests, OverviewTests, AdminOrdersTests; dashboard.test.js |
| US-16 Add favourites | 17 | 4 | AddToWishlistTests, FavouriteStarTests, WineDetailFavouriteButtonTests; wishlist.test.js |
| US-17 Favourites page | 13 | 4 | FavouritesPageTests, ViewManageWishlistTests; wishlist.test.js |
| US-18 Write a review | 27 | 7 | WriteReviewTests, ReviewFromOrderTests, ReviewAuthorNameTests; reviews_modal.test.js |
| US-19 Delete a review | 8 | 0 | DeleteReviewTests, ReviewsSectionTests |
| US-20 Wine quiz | 5 | 7 | WineQuizTests; sommelier_chat.test.js |
| US-21 Recommendations | 6 | 7 | QuizRecommendationTests; sommelier_chat.test.js |
| US-22 SEO | 4 | 0 | SeoTests |
| US-23 Newsletter | 4 | 0 | NewsletterSignupTests |
| US-24 Facebook page | 1 | 0 | FacebookLinkTests |
| US-25 Business model | – | – | Documentation (this README) |
| US-26 Homepage | 15 | 14 | HomepageTests, PagePerformanceTests, PromoBarTests, ErrorPageTests, ValidHtmlTests; carousel.test.js, main.test.js |
| US-27 Static pages | 16 | 0 | ContactFormTests, StaticPagesTests, ShippingPageTests, MessagesSectionTests |
| US-28 Responsive design | – | – | Manual testing at 390, 768, 1280 and 1440px, and Lighthouse |
| US-29 Explore by country | 13 | 9 | CountryFilterTests, CountryLinkEncodingTests, CountriesContextProcessorTests; country_map.test.js |
| US-30 Order email | 3 | 0 | OrderConfirmationEmailTests, StripeWebhookTests |

### Manual testing

I tested the live site by hand on desktop and phone sizes (390, 768, 1280 and 1440px) and with the keyboard only. All tests passed.

| # | User story | Test | Expected | Result |
| ---: | --- | --- | --- | --- |
| 1 | US-01 | Sign up with a new email | "Check your email" in the pop-up; confirmation email arrives | ✅ Pass |
| 2 | US-01 | Click the confirmation link, then log in | Account confirmed; logged in | ✅ Pass |
| 3 | US-02 | Log in with a wrong password | Error shown inside the pop-up | ✅ Pass |
| 4 | US-02 | Log out from the profile | Back to the homepage with a message | ✅ Pass |
| 5 | US-02 | Forgot password | Reset email arrives; new password works | ✅ Pass |
| 6 | US-05/06 | Catalogue, then a type from the nav | Only that type shown | ✅ Pass |
| 7 | US-29 | Map country click and nav Country dropdown | Catalogue filtered by that country | ✅ Pass |
| 8 | US-08 | Search a wine name and a country | Matching results; "no results" message for nonsense | ✅ Pass |
| 9 | US-07 | Open a wine page | Details and "You may also like" (same type) | ✅ Pass |
| 10 | US-16/17 | Star a wine, open Favourites | Star fills; wine listed; add to cart and remove work | ✅ Pass |
| 11 | US-10/11 | Add wines to the cart, change quantities | Totals, badge and preview update | ✅ Pass |
| 12 | US-12 | 8 bottles in the cart | 10% discount shown | ✅ Pass |
| 13 | US-12 | Guest checkout with a Dublin Eircode | €5.95 delivery, or free over €100 | ✅ Pass |
| 14 | US-12 | Invalid Eircode | Clear error, no order created | ✅ Pass |
| 15 | US-13/30 | Pay with 4242 4242 4242 4242 | Success page; order paid; confirmation email | ✅ Pass |
| 16 | US-14 | Pay with 4000 0000 0000 0002 | Error shown; cart kept; order pending | ✅ Pass |
| 17 | US-03 | Edit delivery details, open an order | Saved; order detail with totals | ✅ Pass |
| 18 | US-18 | Write and edit a review from the order page | Shown on the wine page as verified, name not email | ✅ Pass |
| 19 | US-19 | Delete the review from the profile | Confirmation, then removed | ✅ Pass |
| 20 | US-20/21 | Sommelier chat, all 5 questions | Up to 3 recommendations; add to cart works | ✅ Pass |
| 21 | US-23 | Newsletter: valid, duplicate, invalid email | Success / info / error messages | ✅ Pass |
| 22 | US-27 | Contact form | Success message; both emails arrive; message in the dashboard | ✅ Pass |
| 23 | US-09 | Manager: add a wine with an image, edit, delete | Image on Cloudinary; changes visible; delete confirmation | ✅ Pass |
| 24 | US-15 | Manager: change an order to Shipped | Status updated | ✅ Pass |
| 25 | US-04 | Manager opens `/admin/` | Access refused | ✅ Pass |
| 26 | US-04 | Customer opens `/dashboard/` | Redirected with a message | ✅ Pass |
| 27 | US-22 | `/robots.txt` and `/sitemap.xml` | Both load correctly | ✅ Pass |
| 28 | US-26 | Promo bar, carousels, map, Back button | All work | ✅ Pass |
| 29 | US-28 | Key pages at 390, 768, 1280 and 1440px | No overflow, layouts correct | ✅ Pass |
| 30 | Accessibility | Keyboard only through nav, pop-ups, cart | Everything reachable, focus visible, Escape closes pop-ups | ✅ Pass |

### Validation

Full reports are in [docs/validation/](docs/validation/).

| Check | Result | Report |
| --- | --- | --- |
| HTML (W3C Nu checker) | 34 pages, 0 errors, 0 warnings | [html-report.md](docs/validation/html-report.md), [screenshots](docs/validation/screenshots/) |
| CSS (W3C Jigsaw) | Valid CSS level 3, 0 errors (107 expected warnings, explained) | [css-report.md](docs/validation/css-report.md) |
| JavaScript (JSHint) | 11 files, 0 issues | [js-report.md](docs/validation/js-report.md) |
| Python (PEP 8, flake8) | 0 issues | `flake8` |
| Lighthouse | See below | [lighthouse.md](docs/validation/lighthouse.md) |

HTML was checked in two ways: the public pages on the live site by address, and the logged-in pages with my own management command, `python manage.py validate_html --customer <email> --manager <email>`, which renders every page with Django's test client and sends it to the W3C checker.

#### Lighthouse (live site)

| Page | Device | Performance | Accessibility | Best practices | SEO |
| --- | --- | ---: | ---: | ---: | ---: |
| Homepage | Mobile | 73 | 100 | 100 | 100 |
| Homepage | Desktop | 88 | 100 | 100 | 100 |
| Catalogue | Mobile | 83 | 100 | 100 | 100 |
| Catalogue | Desktop | 88 | 100 | 100 | 100 |
| Wine page | Mobile | 86 | 96 | 100 | 100 |
| Wine page | Desktop | 92 | 96 | 100 | 100 |
| Cart | Mobile | 88 | 96 | 100 | 69 |
| Cart | Desktop | 94 | 100 | 100 | 69 |

Known results:

- **Cart SEO 69** is deliberate: the cart is a personal page with `noindex`.
- **Accessibility 96** on some runs is a timing artefact: Lighthouse sometimes measures the rotating promo text mid-fade, when it is almost transparent. At rest it has full contrast, and people who prefer reduced motion get a still message.
- **Homepage mobile performance** is limited mainly by render-blocking stylesheets (Bootstrap, Bootstrap Icons, Google Fonts and the site CSS) and by the larger card images that high-density phones choose. The server responds quickly, pages are gzipped and the hero is a small WebP.

### Bugs fixed

| Bug | Cause | Fix |
| --- | --- | --- |
| Checkout crashed with "Object of type Decimal is not JSON serializable" | The cart saved Decimal prices in the session, which is stored as JSON | The session now only holds strings and whole numbers; Decimals are created when the cart is read |
| Stripe webhook failed on valid events | Stripe's event objects aren't dictionaries, so `.get()` didn't work | The event is converted with `to_dict()` before reading it, and the webhook now logs each event |
| Paid orders stayed "pending" | The Stripe endpoint pointed to `/order/webhook/`, which returned 404, so Stripe kept retrying and the orders were never marked paid. I found it with `heroku logs` and a `curl` POST to each path (400 means the route exists, 404 means the path is wrong) | The real route is `/webhook/`; I updated the endpoint URL in Stripe |
| Migration adding order numbers failed | A unique UUID field with a default gives every existing order the same value | The migration adds the field as optional, generates a UUID for each existing order, then makes it unique |
| The promo bar stopped rotating on the homepage | The homepage's `{% block scripts %}` replaced the one in `base.html`, which loads `main.js` | The block starts with `{{ block.super }}`; later I moved all the JavaScript into separate files in `static/js/` |
| Every page used the homepage grid on desktop | The desktop grid was applied to all `main` elements | It's limited to the homepage with `main:has(> .hero)` |
| Country links broke for names with spaces (e.g. "Czech Republic") | Query values weren't URL-encoded | Templates use the `urlencode` filter and JavaScript uses `encodeURIComponent` |

### Deployment challenges

| Challenge | What I did |
| --- | --- |
| I lost access to the AWS account that stored the production media on Amazon S3 | Moved the media to Cloudinary with a custom storage that keeps Django's file names, and wrote the `upload_media` command to upload the local `media/` folder |
| The Heroku Postgres add-on is paid | Moved the database to a free Neon PostgreSQL database, connected through `DATABASE_URL` |
| The Heroku build failed at `collectstatic`: Django 6.1's new `MAILERS` email setting conflicted with the old `EMAIL_*` settings | Replaced the old settings with a single `MAILERS` configuration (Gmail SMTP when the password is set, the console otherwise) |
| OneDrive turned some test files into cloud-only placeholders, so Jest found fewer test files than exist | Saved the files again as normal local files (contents unchanged) so every test file is found |

### Known issues

- Lighthouse can measure the promo text mid-fade, so accessibility scores 96 on some runs. At rest the text has full contrast, and reduced motion is respected.
- Homepage mobile performance is limited by render-blocking stylesheets (Bootstrap, Bootstrap Icons, Google Fonts and the site CSS).
- The free Neon database can take a moment to respond after being idle.
- Delivery is Ireland only, by design.
- The W3C checker's API sometimes refuses automated requests from scripts (HTTP 429); `validate_html` then keeps the last complete report and asks you to try again later.
- The Facebook link points to facebook.com because the business page is a mockup.

---

## Deployment

### Local setup

1. Clone the repository and open it:

   ```bash
   git clone https://github.com/crucioltheresa/uncorked.git
   cd uncorked
   ```

2. Create and activate a virtual environment, then install the requirements:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows (source .venv/bin/activate on macOS/Linux)
   pip install -r requirements.txt
   npm install                    # for Jest and JSHint
   ```

3. Create a `.env` file in the project root with the environment variables below. Without `DATABASE_URL` the site uses a local SQLite database; without `EMAIL_HOST_PASS` emails are printed in the terminal.
4. Run the migrations, load the wines and create a superuser:

   ```bash
   python manage.py migrate
   python manage.py loaddata wines_fixture
   python manage.py createsuperuser
   python manage.py runserver
   ```

### Environment variables

Only the names are listed here; the values are never committed.

| Name | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for local development only |
| `DATABASE_URL` | Neon PostgreSQL connection URL (production) |
| `CLOUDINARY_URL` | Cloudinary account URL for wine images |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Signing secret of the Stripe webhook endpoint |
| `EMAIL_HOST_USER` | Gmail address that sends the emails |
| `EMAIL_HOST_PASS` | Gmail app password |

### Heroku

1. Create a new app on Heroku.
2. In **Settings → Config Vars**, add all the variables above except `DEBUG`.
3. Connect the GitHub repository in the **Deploy** tab (or push with the Heroku CLI) and deploy the `main` branch. Heroku installs `requirements.txt`, uses the Python version in `.python-version`, collects the static files (served by WhiteNoise) and starts Gunicorn from the `Procfile`.
4. Run the migrations and load the wines once:

   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py loaddata wines_fixture
   heroku run python manage.py createsuperuser
   ```

### Neon database

Create a project on [Neon](https://neon.tech/), copy its PostgreSQL connection string and use it as `DATABASE_URL`.

### Cloudinary

Create a Cloudinary account and use its API environment variable as `CLOUDINARY_URL`. New wine photos uploaded from the site go straight to Cloudinary. To upload the existing local `media/` folder with the same file names the database uses, run:

```bash
python manage.py upload_media
```

### Stripe webhook

1. In the Stripe dashboard, add a webhook endpoint pointing to `https://<your-app>.herokuapp.com/webhook/`.
2. Select the `payment_intent.succeeded` event.
3. Copy the endpoint's signing secret into `STRIPE_WEBHOOK_SECRET`.

### Gmail app password

Turn on 2-Step Verification for the Gmail account, create an **app password** in the Google account's security settings and use it as `EMAIL_HOST_PASS`, with the address as `EMAIL_HOST_USER`.

### Store Managers

The migrations create the **Store Manager** group with the dashboard permission. To give a member of staff access, add their account to that group in the Django admin.

### Forking or cloning

To fork, use **Fork** on the [GitHub repository](https://github.com/crucioltheresa/uncorked); to clone, copy the repository URL from **Code** and run `git clone` as above.

---

## Credits

### Code

- The [Django](https://docs.djangoproject.com/), [django-allauth](https://docs.allauth.org/), [Stripe](https://docs.stripe.com/) and [Cloudinary](https://cloudinary.com/documentation) documentation.
- Code Institute's **Boutique Ado** walkthrough project, which gave me the structure for the e-commerce flow: the cart in the session, checkout with Stripe, webhooks and user profiles.
- My previous project, [Tag Rugby League Manager](https://github.com/crucioltheresa/tag-rugby-league-manager), for the testing style: a `tests.py` in each app and Jest for the JavaScript.

### Libraries

Bootstrap, Bootstrap Icons, Google Fonts, Simple Icons and the Python packages listed in [Technologies](#technologies).

### World map

The interactive world map uses:

- Map data derived from [Natural Earth](https://www.naturalearthdata.com/) (public domain), built collaboratively by USGS, NOAA and Natural Earth contributors.
- SVG processing based on [world-atlas](https://github.com/topojson/world-atlas) (ISC License).

### Fonts

Plaster, Playfair Display and DM Sans from [Google Fonts](https://fonts.google.com/) (SIL Open Font License).

### Images

- **Photos** (hero, editorial strips, sommelier section and wines): photos sourced from Pinterest and used for educational, non-commercial purposes only. All rights belong to their original creators.
- **Award logos**: award logos are used for illustrative purposes only. Uncorked is a fictional shop with no affiliation with these organisations.
- **Payment logos**: [Simple Icons](https://simpleicons.org/).

### Acknowledgements

- My best friends, who always believed in me and supported me throughout this learning journey.
- The Code Institute community, for their help and encouragement along the way.
