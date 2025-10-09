from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

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
    save_percents = models.IntegerField(_("save %"), null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    