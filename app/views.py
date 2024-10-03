from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpRequest, HttpResponse
from .models import User, UserFollows
from django.contrib.auth import login, authenticate, logout as django_logout
from django.contrib.auth.decorators import login_required
from .forms import AuthForm, RegisterForm
from django.utils.translation import gettext as _
from django.db import IntegrityError
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
            logger.debug(f"registration form is valid: username={username}, password={password}")
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
            logger.debug(f"registration form is NOT valid: {register_form.errors.as_text()}")
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
    """disconnect current user and redirect to index
    """
    django_logout(request)
    return redirect("index")


@login_required
def feed(request: HttpRequest):
    """Display the user's feed (todo)."""
    context = {
        "username": request.user.username,
        "feed_entries": feed_tools.feed_entries(request.user)
    }
    return render(request, "app/feed/feed.html", context)


@login_required
def subscriptions_view(request: HttpRequest):
    """Display the subscription page to subscribe to other users.
    """
    context = {
        'following': [],
        'followers': []
    }
    for u in subscription_tools.followed_users(request.user):
        context['following'].append({
            'user_id': u.pk,
            'username': u.username
        })
    for u in subscription_tools.followers(request.user):
        context['followers'].append({
            'username': u.username
        })
    return render(request, "app/subscriptions/subscriptions.html", context=context)


@login_required
def subscription_follow(request: HttpRequest, follow_user_id: int):
    """Follow a user
    """


@login_required
def subscription_cancel(request: HttpRequest, followed_user_id: int):
    """Cancel subscription to another user's posts.
    """
    followed = User.objects.get(pk=followed_user_id)
    followedR = UserFollows.objects.get(user=request.user, followed_user_id=followed_user_id)
    if followed:
        return HttpResponse(f"cancel subscription #{followedR.pk} to {followed.username}")
    else:
        return HttpResponse(f"Subscription to {followed_user_id} not found !")
