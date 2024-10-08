from itertools import chain
from urllib import parse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from .models import User, Ticket
from . import models
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import urls
from . import forms
from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist
from . import feed as feed_tools
from . import subscriptions as subscription_tools
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def index(request: HttpRequest) -> HttpResponse:
    """Default landing page: display auhtentication form and link to registration,
    or redirect to feed if user is authenticated.
    """
    if not request.user.is_authenticated:
        return redirect("auth")
    else:
        return redirect("feed")


@login_required
def feed(request: HttpRequest) -> HttpResponse:
    """Display the user's feed (todo)."""
    context = {
        "username": request.user.username,
        "feed_entries": feed_tools.feed_entries(request.user),
    }
    return render(request, "app/feed/feed.html", context)


@login_required
def subscriptions(request: HttpRequest) -> forms.SubscribeToUserForm:
    """Display the subscription page to subscribe to other users."""
    if request.method == "POST":
        subscribe_form = _handle_subscription_form(request)
    else:
        subscribe_form = forms.SubscribeToUserForm()
    following = [
        {"user_id": u.pk, "username": u.username}
        for u in subscription_tools.followed_users(request.user)
    ]
    followers = [
        {"username": u.username} for u in subscription_tools.followers(request.user)
    ]
    context = {
        "subscribe_form": subscribe_form,
        "following": following,
        "followers": followers,
        "username": request.user.username,
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
def subscription_cancel(request: HttpRequest, followed_user_id: int) -> HttpResponse:
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


@login_required
def edit_ticket(request: HttpRequest, ticket_id: int = None) -> HttpResponse:
    """Edit an existing ticket or create a new ticket."""
    # select the usecase:
    if ticket_id is not None:
        # edit existing ticket
        usecase = "update"
        ticket_instance = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
        edit_url = urls.reverse("edit_ticket", kwargs={"ticket_id": ticket_id})
        success_msg_tpl = _("Updated ticket #%(ticket_id)i: %(ticket_title)s")
    else:
        # create a new ticket
        usecase = "create"
        ticket_instance = Ticket(user=request.user)
        edit_url = urls.reverse("new_ticket")
        success_msg_tpl = _("Created a new ticket #%(ticket_id)i: %(ticket_title)s")

    if request.POST.get("action") == "edit_ticket":
        # handle the form
        form = forms.EditTicketForm(
            request.POST, request.FILES, instance=ticket_instance
        )
        if form.is_valid():
            updated_ticket: Ticket = form.save()
            if updated_ticket:
                success_msg = success_msg_tpl % {
                    "ticket_id": updated_ticket.pk,
                    "ticket_title": updated_ticket.title,
                }
                messages.success(request, success_msg)
                return _redirect_next(request, "feed")
    else:
        form = forms.EditTicketForm(instance=ticket_instance)
    context = {
        "username": request.user.username,
        "usecase": usecase,
        "ticket_form": form,
        "ticket_id": ticket_id,
        "edit_url": _add_next_url(edit_url, request),
    }
    return render(request, "app/posts/edit_ticket.html", context)


@login_required
def delete_ticket(request: HttpRequest, ticket_id: int):
    """Deletes a ticket belonging to the current user."""
    ticket: Ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    ticket.delete()
    messages.success(
        request,
        _("Ticket #%(ticket_id)i deleted: %(ticket_title)s")
        % {"ticket_id": ticket_id, "ticket_title": ticket.title},
    )
    return _redirect_next(request, "feed")


@login_required
def review_for_ticket(request: HttpRequest, ticket_id: int):
    """Creates a review in reply to a ticket.
    Ticket must be visible in the user's feed, otherwise the view will raise a 404.
    """
    ticket_instance = get_object_or_404(
        Ticket,
        pk=ticket_id,
        user__in=subscription_tools.followed_users_or_self(user=request.user),
    )
    review_instance = models.Review(ticket=ticket_instance, user=request.user)
    if request.POST.get("action") == "validate_review":
        form = forms.ReviewForm(request.POST, instance=review_instance)
        if form.is_valid():
            review: models.Review = form.save()
            messages.success(
                request,
                _("You posted a new review in reply to ticket #%(ticket_id)d")
                % ({"ticket_id": review.ticket.pk}),
            )
            return redirect("feed")
    else:
        form = forms.ReviewForm(instance=review_instance)
    context = {
        "username": request.user.username,
        "review_form": form,
        "ticket": feed_tools.feed_post_dict(ticket_instance, can_review=False),
        "usecase": "create",
        "edit_url": urls.reverse("review_for_ticket", kwargs={"ticket_id": ticket_id}),
    }
    return render(request, "app/posts/edit_review.html", context)


@login_required
def edit_review(request: HttpRequest, review_id: int):
    """Updates an existing review."""
    review_instance = get_object_or_404(models.Review, pk=review_id, user=request.user)
    if request.POST.get("action") == "validate_review":
        form = forms.ReviewForm(request.POST, instance=review_instance)
        if form.is_valid():
            review: models.Review = form.save()
            messages.success(
                request,
                _("Updated your review in reply to ticket #%(ticket_id)d")
                % ({"ticket_id": review.ticket.pk}),
            )
            return _redirect_next(request, "feed")
    else:
        form = forms.ReviewForm(instance=review_instance)
    edit_url = urls.reverse("edit_review", kwargs={"review_id": review_id})
    context = {
        "username": request.user.username,
        "review_form": form,
        "ticket": feed_tools.feed_post_dict(review_instance.ticket, can_review=False),
        "usecase": "update",
        "edit_url": _add_next_url(edit_url, request),
    }
    return render(request, "app/posts/edit_review.html", context)


@login_required
def create_review(request: HttpRequest):
    """Creates a review from scratch.
    POST data muts also contain the ticket data.
    Both ticket and review data must be valid to update the model.
    Rediretc to user's feed on success.
    """
    if request.POST.get("action") == "validate_review":
        ticket_form = forms.EditTicketForm(
            request.POST, request.FILES, instance=models.Ticket(user=request.user)
        )
        review_form = forms.ReviewForm(
            request.POST, instance=models.Review(user=request.user)
        )
        if ticket_form.is_valid() and review_form.is_valid():
            ticket_instance: models.Ticket = ticket_form.save()
            review_instance: models.Review = review_form.save(commit=False)
            review_instance.ticket = ticket_instance
            review_instance.save()
            messages.success(
                request,
                _("Created a new review for %(ticket_title)s")
                % ({"ticket_title": ticket_instance.title}),
            )
            return redirect("feed")
    else:
        ticket_form = forms.EditTicketForm(instance=models.Ticket(user=request.user))
        review_form = forms.ReviewForm(instance=models.Review(user=request.user))
    context = {
        "username": request.user.username,
        "ticket_form": ticket_form,
        "review_form": review_form,
    }
    return render(request, "app/posts/create_review.html", context=context)


@login_required
def delete_review(request: HttpRequest, review_id: int):
    """Deletes a review written by the current user."""
    review_instance = get_object_or_404(models.Review, pk=review_id, user=request.user)
    review_instance.delete()
    messages.success(
        request,
        _("Deleted Review #%(review_id)d to ticket #%(ticket_id)d")
        % ({"review_id": review_id, "ticket_id": review_instance.ticket.pk}),
    )
    return _redirect_next(request, "feed")


def _redirect_next(request: HttpRequest, default: str) -> HttpResponse:
    return redirect(_get_next_route(request, default))


def _get_next_route(request: HttpRequest, default: str) -> str:
    """Tries to read the next url field in the request.
    Falls back to default value set by the second parameter.
    """
    return request.POST.get("next") or request.GET.get("next") or default


def _add_next_url(url: str, request: HttpRequest, next_url: str = None, default: str = None) -> str:
    """Appends or updates the 'next" query parameter in a URL."""
    next_url = next_url or _get_next_route(request, default)
    if next_url:
        parts = parse.urlsplit(url)
        qs = parse.parse_qs(parts.query) or {}
        qs.update({'next': next_url})
        new_query = parse.urlencode(qs)
        return parse.urlunsplit([parts.scheme, parts.netloc, parts.path, new_query, parts.fragment])


@login_required
def posts(request: HttpRequest) -> HttpResponse:
    """Display all reviews and tickets posted by a user."""
    user_tickets = models.Ticket.objects.filter(user=request.user)
    user_reviews = (
        models.Review.objects.filter(user=request.user)
        .select_related("user")
        .select_related("ticket")
    )

    def set_commands(post_dict: dict):
        """Extend a post entry with edit and delete commands."""
        post_dict["commands"] = {}
        if post_dict.get("type") == "REVIEW":
            post_dict["commands"]["edit_url"] = _add_next_url(
                url=urls.reverse(
                    "edit_review",
                    kwargs={"review_id": post_dict.get("id")}
                    ),
                request=request,
                next_url="post"
            )
            post_dict["commands"]["delete_url"] = _add_next_url(
                url=urls.reverse(
                    "delete_review",
                    kwargs={"review_id": post_dict.get("id")}
                ),
                request=request,
                next_url="posts"
            )
        elif post_dict.get("type") == "TICKET":
            post_dict["commands"]["edit_url"] = _add_next_url(
                url=urls.reverse(
                    "edit_ticket",
                    kwargs={"ticket_id": post_dict.get("id")}
                ),
                request=request,
                next_url="posts")
            post_dict["commands"]["delete_url"] = _add_next_url(
                url=urls.reverse(
                    "delete_ticket",
                    kwargs={"ticket_id": post_dict.get("id")},
                ),
                request=request,
                next_url="posts")
        return post_dict

    posts = sorted(
        chain(
            [
                set_commands(feed_tools.feed_post_dict(x, content_type="TICKET"))
                for x in user_tickets
            ],
            [
                set_commands(feed_tools.feed_post_dict(x, content_type="REVIEW"))
                for x in user_reviews
            ],
        ),
        key=lambda x: x.get("time_created"),
        reverse=True,
    )
    context = {"username": request.user.username, "posts": posts}
    return render(request, "app/posts/posts.html", context=context)
