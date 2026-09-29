from django.utils.functional import SimpleLazyObject

from .models import WishlistItem


def wishlist_wine_ids(request):
    """
    Ids of the wines in the user's wishlist, for the favourite stars.
    Lazy: the single query runs only on pages that render a star, once per
    request however many cards there are. Anonymous users get an empty set.
    """
    user = getattr(request, "user", None)

    def load():
        if user is None or not user.is_authenticated:
            return frozenset()
        return frozenset(
            WishlistItem.objects.filter(user=user).values_list(
                "wine_id", flat=True
            )
        )

    return {"wishlist_wine_ids": SimpleLazyObject(load)}
