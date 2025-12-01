from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from hockey.utils.db_utils import get_team_choices
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "role", "team_id")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set team choices dynamically to avoid database queries at import time
        # Explicitly set widget to Select to show dropdown instead of number input
        if 'team_id' in self.fields:
            team_choices = [('', '---------')] + get_team_choices()
            # Create Select widget with choices
            self.fields['team_id'].widget = forms.Select(choices=team_choices)
            self.fields['team_id'].choices = team_choices


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "role", "team_id")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set team choices dynamically to avoid database queries at import time
        # Explicitly set widget to Select to show dropdown instead of number input
        if 'team_id' in self.fields:
            team_choices = [('', '---------')] + get_team_choices()
            # Create Select widget with choices
            self.fields['team_id'].widget = forms.Select(choices=team_choices)
            self.fields['team_id'].choices = team_choices
        