"""
Django admin configuration for users app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'prn', 'hod_courses')
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = BaseUserAdmin.list_filter + ('role', 'is_active')
    search_fields = BaseUserAdmin.search_fields + ('prn', 'hod_courses')
    ordering = ('-date_joined',)
