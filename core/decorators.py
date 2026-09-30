from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

# Given to the "Store Manager" group; superusers have it automatically
DASHBOARD_PERMISSION = "dashboard.access_dashboard"


def can_manage_store(user):
    """True for superusers and users with the dashboard permission."""
    return user.is_authenticated and user.has_perm(DASHBOARD_PERMISSION)


def store_manager_required(view):
    """
    Store management pages (the Store Dashboard and product management).
    Logged out: send to login. Logged in without the dashboard permission:
    refuse with an error message and send to the catalogue.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not can_manage_store(request.user):
            messages.error(
                request, "Only site administrators can access that page."
            )
            return redirect("wine_list")
        return view(request, *args, **kwargs)

    return wrapper
