from django import forms
from django.core import validators


class SubscribeToUserForm(forms.Form):
    """Subscribe to posts from another user in a user's feed.
    For now we only query a single exact user name found in a text input.
    """
    follow_username = forms.CharField(
        required=True,
        validators=[validators.ProhibitNullCharactersValidator, validators.MaxLengthValidator(150)],
    )
