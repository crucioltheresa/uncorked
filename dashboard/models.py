from django.db import models


class DashboardAccess(models.Model):
    """
    Holds the Store Dashboard permission; it has no table (managed=False).
    Giving a user or group "dashboard.access_dashboard" lets them use the
    Store Dashboard and the product management pages.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("access_dashboard", "Can use the Store Dashboard"),
        ]
