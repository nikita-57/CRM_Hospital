from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("role", "department")}),
    )

    list_display = ("username", "first_name", "last_name", "role", "department", "is_active")
    list_filter = ("role", "department", "is_active")
