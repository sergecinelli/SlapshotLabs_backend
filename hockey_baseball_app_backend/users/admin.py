import datetime

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.conf import settings

from hockey.utils.db_utils import get_team_choices
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, UserInvitation


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


class IsExpiredFilter(admin.SimpleListFilter):
    title = "expired"
    parameter_name = "is_expired"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Expired"),
            ("no", "Not expired"),
        ]

    def queryset(self, request, queryset):
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=settings.INVITATION_EXPIRATION_DAYS)
        if self.value() == "yes":
            return queryset.filter(
                models.Q(invited_at__lt=cutoff) | models.Q(send_email_error_timestamp__lt=cutoff)
            )
        if self.value() == "no":
            return queryset.exclude(
                models.Q(invited_at__lt=cutoff) | models.Q(send_email_error_timestamp__lt=cutoff)
            )
        return queryset


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "invited_by", "invited_at", "send_email_error_timestamp", "is_expired", "send_email_error_message")
    list_filter = ("invited_by", "invited_at", "send_email_error_timestamp", IsExpiredFilter)
    search_fields = ("email", "invited_by__email", "send_email_error_message")
    ordering = ("-send_email_error_timestamp", "-invited_at")


admin.site.register(CustomUser, CustomUserAdmin)
