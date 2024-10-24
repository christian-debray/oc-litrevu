from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.utils.translation import gettext as _
from app.models import User


class AuthForm(forms.Form):
    """Authentication form requires only two fields, username and password.
    Validation process differs from Registration form."""
    username = forms.CharField(
        required=True,
        validators=[validators.ProhibitNullCharactersValidator, validators.MaxLengthValidator(150)],
    )
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        validators=[validators.ProhibitNullCharactersValidator, validators.MaxLengthValidator(128)],
    )

    def clean_username(self):
        """Username is not case-sensitive.
        """
        return self.cleaned_data.get('username').lower()


class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "password"]

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(render_value=False),
        help_text="\n".join(password_validation.password_validators_help_texts())
    )

    password_confirm = forms.CharField(
        required=True,
        widget=forms.PasswordInput(render_value=False),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            self.add_error("username", _("A user with this username already exists."))
        return username

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
        # finally check password confirmation matches:
        password_confirm = self.data.get("password_confirm")
        if (password_confirm is None) or (password != password_confirm):
            raise ValidationError(_("Password and password confirmation must match."), code="invalid")
        return password
