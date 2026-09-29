from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """Delivery details shown on the user's admin page."""

    model = UserProfile
    can_delete = False
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Users log in with their email, so it leads the list and search."""

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_display = (
        "email", "username", "is_staff", "is_active", "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)

    def get_inlines(self, request, obj):
        """
        Profile only when editing: a new user's profile is created by the
        post_save signal, so an inline on the add page would clash with it.
        """
        return [UserProfileInline] if obj else []


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Saved delivery details (Eircode is stored in postcode)."""

    list_display = ("user", "full_name", "city", "postcode", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("user__email", "full_name", "city", "postcode")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
