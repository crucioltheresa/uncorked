from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


def superuser_required(view):
    """
    Store management pages (product management and the Store Dashboard).
    Logged out: send to login. Logged in but not a superuser: refuse with
    an error message and send to the catalogue.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser:
            messages.error(
                request, "Only site administrators can access that page."
            )
            return redirect("wine_list")
        return view(request, *args, **kwargs)

    return wrapper
