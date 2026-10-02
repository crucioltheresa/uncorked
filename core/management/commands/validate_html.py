import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client, override_settings
from django.urls import reverse

from core.models import ContactMessage
from orders.models import Order
from products.models import Wine

VALIDATOR_URL = "https://validator.w3.org/nu/?out=json"
USER_AGENT = (
    "Uncorked-validate_html/1.0 "
    "(HTML validation for the Uncorked wine shop; "
    "+https://github.com/crucioltheresa/uncorked)"
)
DEFAULT_REPORT = Path("docs") / "validation" / "html-report.md"


RETRIES = 3


class Skip(Exception):
    """A page that can't be rendered with the local data."""


class ValidatorUnavailable(Exception):
    """The validator couldn't be reached or kept refusing requests."""


class Command(BaseCommand):
    help = (
        "Render every page of the site with the test client against the "
        "local database, send each page's HTML to the W3C Nu HTML "
        "validator and write docs/validation/html-report.md. Exits with "
        "an error if any page has HTML errors."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--customer", required=True,
            help="Email of a customer account for the logged-in pages.",
        )
        parser.add_argument(
            "--manager", required=True,
            help="Email of a store manager (or superuser) for the dashboard.",
        )
        parser.add_argument(
            "--delay", type=float, default=1.5,
            help="Seconds to wait between validator requests (default 1.5).",
        )
        parser.add_argument(
            "--report", default=str(DEFAULT_REPORT),
            help=f"Markdown report path (default {DEFAULT_REPORT}).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        users = {}
        for role in ("customer", "manager"):
            email = options[role]
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                raise CommandError(f"No user with the email {email} ({role}).")
            users[role] = user
        self.delay = options["delay"]

        # Render as production does (custom 404 page, no debug pages), with
        # plain static file URLs so no collectstatic manifest is needed
        storages = {
            **settings.STORAGES,
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage."
                           "StaticFilesStorage",
            },
        }
        with override_settings(DEBUG=False, STORAGES=storages):
            pages = self.render_pages(users)

        results = []
        validated = 0
        unavailable = None
        for page in pages:
            if page["skipped"]:
                self.stdout.write(f"skip  {page['name']}: {page['skipped']}")
                results.append(page)
                continue
            html = page.pop("html")
            if unavailable is None:
                if validated:
                    time.sleep(self.delay)
                validated += 1
                self.stdout.write(f"check {page['name']} ({page['url']})")
                try:
                    page.update(self.validate(html))
                except ValidatorUnavailable as error:
                    # Stop sending requests to a validator that's refusing
                    unavailable = str(error)
            if unavailable is not None and "errors" not in page:
                # Not an HTML error: the page just couldn't be checked
                page["skipped"] = f"not checked (validator: {unavailable})"
                page["unchecked"] = True
            results.append(page)

        self.print_table(results)
        failing = [r for r in results if not r["skipped"] and r["errors"]]
        unchecked = [r for r in results if r.get("unchecked")]
        report = Path(options["report"])
        if unchecked and report.exists():
            # Keep the last complete report rather than one full of gaps
            self.stdout.write(
                f"\nThe validator was unavailable; {report.as_posix()} "
                "was left as it was."
            )
        else:
            self.write_report(report, results)
            self.stdout.write(f"\nReport written to {report.as_posix()}")

        if failing:
            raise CommandError(
                f"{len(failing)} page(s) have HTML errors: "
                + ", ".join(r["name"] for r in failing)
            )
        if unchecked:
            raise CommandError(
                f"{len(unchecked)} page(s) couldn't be checked because the "
                "validator was unavailable; run the command again later."
            )
        self.stdout.write(self.style.SUCCESS("No HTML errors."))

    # Rendering ------------------------------------------------------------

    def render_pages(self, users):
        """Render every page; each entry has its HTML or a skip reason."""
        pages = []
        public = Client(SERVER_NAME="localhost")
        customer = Client(SERVER_NAME="localhost")
        customer.force_login(users["customer"])
        manager = Client(SERVER_NAME="localhost")
        manager.force_login(users["manager"])

        def add(group, name, client, url_or_fn, expect=200):
            entry = {"group": group, "name": name, "url": "", "skipped": ""}
            try:
                url = url_or_fn() if callable(url_or_fn) else url_or_fn
                entry["url"] = url
                response = client.get(url)
                if response.status_code != expect:
                    where = response.get("Location", "")
                    raise Skip(
                        f"HTTP {response.status_code}"
                        + (f" to {where}" if where else "")
                    )
                entry["html"] = response.content.decode("utf-8")
            except Skip as reason:
                entry["skipped"] = str(reason)
            except Exception as error:  # a page that fails to render
                entry["skipped"] = f"{type(error).__name__}: {error}"
            pages.append(entry)

        def wine():
            found = Wine.objects.filter(is_available=True).order_by("id")
            if not found.exists():
                raise Skip("no available wine")
            return found.first()

        def latest_order():
            order = Order.objects.filter(user=users["customer"]).first()
            if order is None:
                raise Skip("the customer has no orders")
            return order

        def spaced_country():
            country = (
                Wine.objects.filter(
                    is_available=True, region__country__contains=" "
                )
                .order_by("region__country")
                .values_list("region__country", flat=True)
                .first()
            )
            if country is None:
                raise Skip("no country with a space in its name has wines")
            return f"{reverse('wine_list')}?{urlencode({'country': country})}"

        def first_message():
            message = ContactMessage.objects.order_by("id").first()
            if message is None:
                raise Skip("no contact messages")
            return reverse("dashboard:message_detail", args=[message.pk])

        def cart_with_items():
            # Put one bottle in the customer's session cart first
            response = customer.post(
                reverse("cart_add", args=[wine().id]), {"quantity": 1}
            )
            if response.status_code != 302:
                raise Skip(
                    f"adding to the cart gave HTTP {response.status_code}"
                )
            return reverse("cart_detail")

        # Public pages
        add("Public", "Homepage", public, reverse("homepage"))
        add("Public", "Catalogue", public, reverse("wine_list"))
        add("Public", "Catalogue: type", public,
            f"{reverse('wine_list')}?type=red")
        add("Public", "Catalogue: country", public, spaced_country)
        add("Public", "Search results", public,
            f"{reverse('wine_list')}?q=red")
        add("Public", "Wine page", public,
            lambda: reverse("wine_detail", args=[wine().slug]))
        add("Public", "Sommelier", public, reverse("quiz_start"))
        add("Public", "About", public, reverse("about"))
        add("Public", "FAQ", public, reverse("faq"))
        add("Public", "Shipping & Returns", public,
            reverse("shipping_returns"))
        add("Public", "Privacy", public, reverse("privacy"))
        add("Public", "Contact", public, reverse("contact"))
        add("Public", "Login", public, reverse("account_login"))
        add("Public", "Signup", public, reverse("account_signup"))
        add("Public", "Password reset", public,
            reverse("account_reset_password"))
        add("Public", "404", public, "/this-page-does-not-exist/",
            expect=404)

        # Customer pages
        add("Customer", "Wine page (logged in)", customer,
            lambda: reverse("wine_detail", args=[wine().slug]))
        add("Customer", "Cart with items", customer, cart_with_items)
        add("Customer", "Checkout", customer, reverse("checkout"))
        add("Customer", "Profile", customer, reverse("profile"))
        add("Customer", "Order detail", customer,
            lambda: reverse("order_detail",
                            args=[latest_order().order_number]))
        add("Customer", "Favourites", customer, reverse("wishlist_detail"))
        # Last: viewing the success page empties the session cart
        add("Customer", "Order success", customer,
            lambda: reverse("order_success",
                            args=[latest_order().order_number]))

        # Store manager pages
        add("Manager", "Dashboard overview", manager,
            reverse("dashboard:overview"))
        add("Manager", "Dashboard wines", manager, reverse("dashboard:wines"))
        add("Manager", "Dashboard orders", manager,
            reverse("dashboard:orders"))
        add("Manager", "Dashboard order detail", manager,
            lambda: reverse("dashboard:order_detail", args=[
                (Order.objects.first() or self._no("no orders")).order_number
            ]))
        add("Manager", "Dashboard messages", manager,
            reverse("dashboard:messages"))
        add("Manager", "Dashboard message detail", manager, first_message)
        add("Manager", "Dashboard reviews", manager,
            reverse("dashboard:reviews"))
        add("Manager", "Dashboard regions", manager,
            reverse("dashboard:regions"))
        add("Manager", "Add region", manager, reverse("dashboard:region_add"))
        add("Manager", "Add wine", manager, reverse("wine_add"))
        add("Manager", "Edit wine", manager,
            lambda: reverse("wine_edit", args=[wine().slug]))
        add("Manager", "Delete wine (confirmation)", manager,
            lambda: reverse("wine_delete", args=[wine().slug]))
        return pages

    @staticmethod
    def _no(reason):
        raise Skip(reason)

    # Validation -----------------------------------------------------------

    def validate(self, html):
        """Send the HTML to the Nu validator; return errors and warnings."""
        request = urllib.request.Request(
            VALIDATOR_URL,
            data=html.encode("utf-8"),
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        # Retry when the validator is busy (429) or unreachable, waiting as
        # long as it asks (Retry-After) or 30 seconds
        for attempt in range(1, RETRIES + 1):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = json.load(response)
                break
            except (urllib.error.URLError, TimeoutError, ValueError) as error:
                if attempt == RETRIES:
                    raise ValidatorUnavailable(str(error)) from error
                wait = 30
                headers = getattr(error, "headers", None)
                if headers and str(headers.get("Retry-After", "")).isdigit():
                    wait = int(headers["Retry-After"])
                self.stdout.write(f"      {error}; retrying in {wait}s")
                time.sleep(wait)

        errors, warnings = [], []
        for message in data.get("messages", []):
            kind = message.get("type")
            if kind in ("error", "non-document-error"):
                errors.append(message)
            elif kind == "info" and message.get("subType") == "warning":
                warnings.append(message)
        return {"errors": errors, "warnings": warnings}

    # Output ---------------------------------------------------------------

    def print_table(self, results):
        width = max(len(r["name"]) for r in results)
        self.stdout.write("")
        self.stdout.write(f"{'Page':<{width}}  Errors  Warnings")
        self.stdout.write(f"{'-' * width}  ------  --------")
        for r in results:
            if r["skipped"]:
                self.stdout.write(
                    f"{r['name']:<{width}}  skipped ({r['skipped']})"
                )
            else:
                self.stdout.write(
                    f"{r['name']:<{width}}  {len(r['errors']):>6}  "
                    f"{len(r['warnings']):>8}"
                )

    @staticmethod
    def _describe(message):
        """One line for a validator message: where, what and the extract."""
        where = ""
        if message.get("lastLine"):
            where = f"line {message['lastLine']}"
            if message.get("firstColumn"):
                where += f", col {message['firstColumn']}"
            where += ": "
        text = message.get("message", "").replace("\n", " ")
        extract = (message.get("extract") or "").strip().replace("\n", " ")
        line = f"- {where}{text}"
        if extract:
            extract = extract.replace("`", "'")
            line += f"\n  `{extract}`"
        return line

    def write_report(self, path, results):
        checked = [r for r in results if not r["skipped"]]
        skipped = [r for r in results if r["skipped"]]
        total_errors = sum(len(r["errors"]) for r in checked)
        total_warnings = sum(len(r["warnings"]) for r in checked)
        lines = [
            "# HTML validation report",
            "",
            f"Generated on {datetime.now():%d %B %Y at %H:%M} by "
            "`python manage.py validate_html`. Every page was rendered with "
            "Django's test client against the local database and sent to "
            "the [W3C Nu HTML Checker](https://validator.w3.org/nu/).",
            "",
            f"- Pages checked: {len(checked)}",
            f"- Pages skipped: {len(skipped)}",
            f"- Errors: {total_errors}",
            f"- Warnings: {total_warnings}",
            "",
            "| Group | Page | URL | Errors | Warnings |",
            "| --- | --- | --- | ---: | ---: |",
        ]
        for r in results:
            url = f"`{r['url']}`" if r["url"] else ""
            if r["skipped"]:
                lines.append(
                    f"| {r['group']} | {r['name']} | {url} | skipped | "
                    f"{r['skipped']} |"
                )
            else:
                status = "✅ 0" if not r["errors"] else str(len(r["errors"]))
                lines.append(
                    f"| {r['group']} | {r['name']} | {url} | {status} | "
                    f"{len(r['warnings'])} |"
                )

        lines += ["", "## Errors by page", ""]
        with_errors = [r for r in checked if r["errors"]]
        if not with_errors:
            lines.append("No errors.")
        for r in with_errors:
            lines += [f"### {r['name']} (`{r['url']}`)", ""]
            lines += [self._describe(m) for m in r["errors"]]
            lines.append("")

        with_warnings = [r for r in checked if r["warnings"]]
        if with_warnings:
            lines += ["## Warnings by page", ""]
            for r in with_warnings:
                lines += [f"### {r['name']} (`{r['url']}`)", ""]
                lines += [self._describe(m) for m in r["warnings"]]
                lines.append("")

        if skipped:
            lines += ["## Skipped pages", ""]
            lines += [f"- {r['name']}: {r['skipped']}" for r in skipped]
            lines.append("")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
