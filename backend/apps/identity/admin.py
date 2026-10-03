from django.contrib import admin
from apps.identity.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "is_staff",
        "is_active",
        "email_verified",
        "created_at",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "email_verified",
    )
    search_fields = ("email",)
    ordering = ("-created_at",)
