from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from hockey.utils.db_utils import get_team_choices
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ("email", "role", "is_staff", "is_superuser", "is_active",)
    list_filter = ("role", "is_staff", "is_superuser", "is_active",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "role", "team_id")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "first_name", "last_name", "role", "team_id",
                "is_staff", "is_superuser", "is_active", "groups", "user_permissions"
            )}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Override to ensure team_id uses a Select widget with team choices."""
        if db_field.name == 'team_id':
            # Get team choices
            team_choices = [('', '---------')] + get_team_choices()
            # Get the default formfield first
            formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
            # Replace widget with Select that has choices, and set field choices
            formfield.widget = forms.Select(choices=team_choices)
            formfield.choices = team_choices
            return formfield
        return super().formfield_for_dbfield(db_field, request, **kwargs)


admin.site.register(CustomUser, CustomUserAdmin)
