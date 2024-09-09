from django import forms
from django.core import validators
from .models import User


class AuthForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        validators=[validators.ProhibitNullCharactersValidator],
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(render_value=False),
        validators=[validators.ProhibitNullCharactersValidator],
    )


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password"]
        widgets = {"password": forms.PasswordInput(render_value=False)}
