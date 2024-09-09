from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse, HttpRequest
from .models import User
from django.contrib.auth import login, authenticate
from .forms import AuthForm, RegisterForm
from django.utils.translation import gettext as _
from django.db import IntegrityError
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def index(request: HttpRequest):
    """Default landing page: display auhtentication form and link to registration,
    or redirect to feed if user is authenticated.
    """
    if request.user.is_authenticated:
        redirect("feed")
    context = {}
    context['auth_form'] = AuthForm()
    return render(request, "app/index.html", context)


def register(request: HttpRequest):
    """Register a new user and redirect to user feed on success.
    """
    context = {}
    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get("username")
            password = register_form.cleaned_data.get("password")
            try:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                login(request=request, user=user)
                return redirect("feed")
            except IntegrityError as e:
                register_form.add_error(field="username", error=e)
            except Exception as e:
                register_form.add_error(field=None, error=e)
    else:
        register_form = RegisterForm()
    context['register_form'] = register_form
    return render(request, "app/auth/register.html", context)


def auth(request: HttpRequest):
    """Autenticate an existing user and redirect to user feed on success.
    """
    context = {}
    if request.method == "POST":
        auth_form = AuthForm(request.POST)
        if auth_form.is_valid():
            username = auth_form.cleaned_data.get("username")
            password = auth_form.cleaned_data.get("password")
            user = authenticate(request=request, username=username, password=password)
            if user is not None:
                login(request=request, user=user)
                return redirect("feed")
            else:
                auth_form.add_error(field=None, error=_("Wrong login"))
    else:
        auth_form = AuthForm()
    context['auth_form'] = auth_form
    return render(request, "app/index.html", context)


def feed(request: HttpRequest):
    """Display the user's feed (todo).
    """
    # TODO: implement the user feed
    if not (request.user and request.user.is_authenticated):
        return redirect("auth")
    return HttpResponse(content=f"Welcome {request.user}")
