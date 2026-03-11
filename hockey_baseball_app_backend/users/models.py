import uuid
import datetime
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from users.utils.roles import Role, get_constant_class_int_choices

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    phone_number = PhoneNumberField(_("phone number"), blank=True)
    country = models.CharField(_("country"), max_length=100)
    region = models.CharField(_("province/state"), max_length=100)
    city = models.CharField(_("city"), max_length=100)
    street = models.CharField(_("street"), max_length=200, blank=True)
    postal_code = models.CharField(_("postal/zip code"), max_length=50, blank=True)

    role = models.IntegerField("Website role", choices=get_constant_class_int_choices(Role), default=Role.PLAYER.id)
    team_id = models.IntegerField("Team", null=True, blank=True)

    gamesheet_seasonid = models.TextField("Gamesheet season ID", null=True, blank=True)
    """ID of the season in the Gamesheet iframe."""

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class UserInvitation(models.Model):
    email = models.EmailField(db_index=True)
    """Email of the user invited to access the website."""

    invited_at = models.DateTimeField(null=True, blank=True, db_index=True)
    """Date and time the user was invited. If not set, send email has failed."""

    invited_by = models.ForeignKey(CustomUser, related_name='invitations_sent', on_delete=models.CASCADE)
    """User who invited the user to access the website."""

    invitation_token = models.UUIDField(default=uuid.uuid4, editable=False)
    """Token for the invitation. Used to access the website. Generated automatically."""

    invitation_details = models.JSONField(null=True, blank=True)
    """Details of the invitation. For example, the analytics ID if the invitation is for access to an analytics."""

    send_email_error_message = models.TextField(null=True, blank=True)
    """Error message if the email sending failed."""

    send_email_error_traceback = models.TextField(null=True, blank=True)
    """Traceback if the email sending failed."""

    send_email_error_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    """Timestamp if the email sending failed."""

    def is_expired(self) -> bool:
        """Check if the invitation is expired. 
        The invitation is expired if the user was invited more than `settings.INVITATION_EXPIRATION_DAYS` days ago 
        or if the email sending failed more than `settings.INVITATION_EXPIRATION_DAYS` days ago.
        If the invitation is expired, it should be deleted."""
        return (self.invited_at is not None and
                self.invited_at < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=settings.INVITATION_EXPIRATION_DAYS) or
                self.send_email_error_timestamp is not None and
                self.send_email_error_timestamp < datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=settings.INVITATION_EXPIRATION_DAYS))

    def __str__(self):
        return f"{self.invited_by.email} - {self.email} - {self.invited_at}"

    class Meta:
        db_table = "user_invitation"
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'invited_by', 'invitation_details'],
                name='unique_user_invitation'
            )
        ]