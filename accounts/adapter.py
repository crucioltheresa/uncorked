from allauth.account import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


def _duration(seconds):
    """Readable duration for email copy, e.g. "3 days" or "1 hour"."""
    days, remainder = divmod(int(seconds), 86400)
    if days and not remainder:
        return f"{days} day{'s' if days != 1 else ''}"
    hours = max(1, round(seconds / 3600))
    return f"{hours} hour{'s' if hours != 1 else ''}"


class AccountAdapter(DefaultAccountAdapter):
    """Adds link expiry times and a greeting name to account emails."""

    def send_mail(self, template_prefix, email, context):
        context = dict(context)
        context["confirmation_expiry"] = _duration(
            app_settings.EMAIL_CONFIRMATION_EXPIRE_DAYS * 86400
        )
        context["password_reset_expiry"] = _duration(
            settings.PASSWORD_RESET_TIMEOUT
        )
        # Usernames are auto-generated, so greet by first name or not at all
        user = context.get("user")
        context["greeting_name"] = getattr(user, "first_name", "") or ""
        super().send_mail(template_prefix, email, context)
