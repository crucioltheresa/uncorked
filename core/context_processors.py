from django.utils.functional import SimpleLazyObject

from .decorators import can_manage_store


def store_roles(request):
    """
    can_manage_store: may use the Store Dashboard and product management
    (superusers and the "Store Manager" group).
    is_store_manager: has that access without being a superuser, so the
    account area is the dashboard rather than the customer profile.
    Both are lazy: the permission lookup only runs if a template uses them.
    """
    user = getattr(request, "user", None)

    def manages():
        return user is not None and can_manage_store(user)

    def manager_only():
        return manages() and not user.is_superuser

    return {
        "can_manage_store": SimpleLazyObject(manages),
        "is_store_manager": SimpleLazyObject(manager_only),
    }
