from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from app.models import User
from django.utils.translation import gettext as _
from django.contrib.auth import login, authenticate, logout as django_logout, password_validation
from .forms import AuthForm, RegisterForm
from django.db import IntegrityError
import logging

logger = logging.getLogger()


def register(request: HttpRequest):
    """Register a new user and redirect to user feed on success."""
    context = {}
    if request.POST.get('action') == "register":
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get("username").lower()
            display_name = register_form.cleaned_data.get("username")
            password = register_form.cleaned_data.get("password")
            try:
                user = User.objects.create_user(username=username, display_name=display_name, password=password)
                user.save()
                login(request=request, user=user)
                return _redirect_after_authentication(request)
            except IntegrityError as e:
                register_form.add_error(field="username", error=e)
            except Exception as e:
                register_form.add_error(field=None, error=e)
    else:
        register_form = RegisterForm()
    context["register_form"] = register_form
    context["password_help_text"] = password_validation.password_validators_help_texts()
    context["redirect_after_login"] = _redirect_url(request)
    return render(request, "app/register.html", context)


def auth(request: HttpRequest):
    """Autenticate an existing user and redirect to user feed on success."""
    context = {}
    if request.POST.get('action') == "login":
        auth_form = AuthForm(request.POST)
        if auth_form.is_valid():
            username = auth_form.cleaned_data.get("username").lower()
            password = auth_form.cleaned_data.get("password")
            user = authenticate(request=request, username=username, password=password)
            if user is not None:
                login(request=request, user=user)
                return _redirect_after_authentication(request)
            else:
                auth_form.add_error(field=None, error=_("Wrong login"))
        else:
            auth_form.add_error(field=None, error="Invalid data")
    else:
        auth_form = AuthForm()
    context["auth_form"] = auth_form
    context["redirect_after_login"] = _redirect_url(request)
    return render(request, "app/index.html", context)


def _redirect_url(request: HttpRequest) -> str:
    return request.POST.get("next", request.GET.get("next", "index"))


def _redirect_after_authentication(request: HttpRequest) -> HttpResponse:
    """Returns a redirect to urla fter successful authentication.
    Tries to read a "next" field in the query params if available,
    falls back to "index" otherwise.
    """
    redirect_url = _redirect_url(request)
    logger.debug(f"Redirect after login: next = {redirect_url}")
    if not redirect_url:
        redirect_url = "index"
    logger.debug(f"Redirect to {redirect_url}...")
    return redirect(redirect_url)


def logout(request: HttpRequest):
    """Disconnect current user and redirect to index."""
    django_logout(request)
    return redirect("index")
