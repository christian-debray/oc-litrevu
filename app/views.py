from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpRequest
from .models import User

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from . import forms
from django.utils.translation import gettext as _
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
        "followers": followers,
        "username": request.user.username
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
