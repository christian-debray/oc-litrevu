from django import forms


class AuthForm(forms.Form):
    login = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False))


class RegisterForm(forms.Form):
    login = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False))
