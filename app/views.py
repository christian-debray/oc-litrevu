from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpRequest
from .models import User
from django.contrib.auth import login, authenticate, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AuthForm, RegisterForm
from . import forms
from django.utils.translation import gettext as _
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from . import feed as feed_tools
from . import subscriptions as subscription_tools
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def index(request: HttpRequest):
    """Default landing page: display auhtentication form and link to registration,
    or redirect to feed if user is authenticated.
    """
    if not request.user.is_authenticated:
        return redirect("auth")
    else:
        return redirect("feed")


def register(request: HttpRequest):
    """Register a new user and redirect to user feed on success."""
    context = {}
    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data.get("username")
            password = register_form.cleaned_data.get("password")
            logger.debug(
                f"registration form is valid: username={username}, password={password}"
            )
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
            logger.debug(
                f"registration form is NOT valid: {register_form.errors.as_text()}"
            )
    else:
        register_form = RegisterForm()
    context["register_form"] = register_form
    return render(request, "app/auth/register.html", context)


def auth(request: HttpRequest):
    """Autenticate an existing user and redirect to user feed on success."""
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
            auth_form.add_error(field=None, error="Invalid data")
    else:
        auth_form = AuthForm()
    context["auth_form"] = auth_form
    return render(request, "app/index.html", context)


def logout(request: HttpRequest):
    """disconnect current user and redirect to index"""
    django_logout(request)
    return redirect("index")


@login_required
def feed(request: HttpRequest):
    """Display the user's feed (todo)."""
    context = {
        "username": request.user.username,
        "feed_entries": feed_tools.feed_entries(request.user),
    }
    return render(request, "app/feed/feed.html", context)


@login_required
def subscriptions(request: HttpRequest):
    """Display the subscription page to subscribe to other users.
    """
    if request.method == "POST":
        subscribe_form = _handle_subscription_form(request)
    else:
        subscribe_form = forms.SubscribeToUserForm()
    following = [{"user_id": u.pk, "username": u.username} for u in subscription_tools.followed_users(request.user)]
    followers = [{"username": u.username} for u in subscription_tools.followers(request.user)]
    context = {
        "subscribe_form": subscribe_form,
        "following": following,
        "followers": followers
    }
    return render(request, "app/subscriptions/subscriptions.html", context=context)


def _handle_subscription_form(request: HttpRequest):
    """Handles the subscription request found in the subscribe form data
    and returns the form object."""
    form = forms.SubscribeToUserForm(request.POST)
    if form.is_valid():
        follow_username = form.cleaned_data.get("follow_username")
        try:
            subscription_tools.subscribe_to_user(request.user, follow_username)
            success_msg = _("You are now following %(username)s") % {
                "username": follow_username
            }
            messages.success(request, success_msg)
        except ObjectDoesNotExist:
            messages.error(request, _("Operation failed!"))
            form.add_error(
                field="follow_username",
                error=_("User does not exist or is already being followed."),
            )
    return form


@login_required
def subscription_cancel(request: HttpRequest, followed_user_id: int):
    """Cancel subscription to another user's posts."""
    try:
        followed_username = User.objects.get(pk=followed_user_id).username
        if subscription_tools.cancel_subscription(
            request.user, followed_user_id=followed_user_id
        ):
            success_msg = _("Canceled subscription to %(followed_username)s.") % {
                "followed_username": followed_username
            }
            messages.success(request, success_msg)
        else:
            messages.error(request, _("Failed to cancel a subscription !"))
    except ObjectDoesNotExist:
        messages.error(request, _("Subscription not found !"))
    return redirect("subscriptions")
