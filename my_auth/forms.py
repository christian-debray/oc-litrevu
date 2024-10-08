from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.utils.translation import gettext as _
# from .validators import password_strength_validator
from app.models import User


class AuthForm(forms.Form):
    """Authentication form requires only two fields, user and password.
    Validation process differs from Registration form, ."""
    username = forms.CharField(
        required=True,
        validators=[validators.ProhibitNullCharactersValidator, validators.MaxLengthValidator(150)],
    )
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        validators=[validators.ProhibitNullCharactersValidator, validators.MaxLengthValidator(128)],
    )


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password"]
        widgets = {"password": forms.PasswordInput(render_value=False)}

    password_confirm = forms.CharField(
        required=True,
        widget=forms.PasswordInput(render_value=False)
    )

    def clean_password(self):
        """Validate a password: see AUTH_PASSWORD_VALIDATORS in settings.py
        """
        password = self.cleaned_data.get("password")
        if not password:
            raise ValidationError(_("Missing or invalid password"), code="invalid")
        username = self.cleaned_data.get("username")
        if not username:
            raise ValidationError(_("Missing or invalid username"), code="invalid")
        # some password validators require a User object: UserAttributeSimilarityValidator
        test_user = User(username=username, password=password)
        password_validation.validate_password(password, user=test_user)
        # also use our custom password strength validation
        # password_strength_validator(password=password, min_lower=1, min_upper=1, min_digit=1, min_special=1)
        return password

    def clean_password_confirm(self):
        """Validate password confirmation"""
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if (password_confirm is None) or (password != password_confirm):
            raise ValidationError(_("Password and password confirmation must match."), code="invalid")
        return password_confirm
