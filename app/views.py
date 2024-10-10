from itertools import chain
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from .models import User, Ticket, Review
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import urls
from . import forms
from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist
from . import feed as feed_tools
from . import subscriptions as subscription_tools
from . import posts as post_tools
from . import helpers
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
    u_list = subscription_tools.followed_users_or_self(request.user)
    tickets = Ticket.with_user_manager.own_or_followed(request.user)
    reviews = feed_tools.feed_reviews(user=request.user, following=u_list)
    entries = sorted(
        chain(tickets, reviews), key=lambda x: x.time_created, reverse=True
    )
    context = {"feed_entries": entries, "display_commands": False}
    return render(request, "app/feed/feed.html", context)


@login_required
def subscriptions(request: HttpRequest) -> forms.SubscribeToUserForm:
    """Display the subscription page to subscribe to other users."""
    if request.POST.get("action") == "validate_subscription":
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
def create_ticket(request: HttpRequest) -> HttpResponse:
    """Create a new Ticket"""
    ticket_instance = Ticket(user=request.user)
    edit_url = urls.reverse("new_ticket")
    success_msg_tpl = _("Created a new ticket #%(ticket_id)i: %(ticket_title)s")
    return _edit_or_create_ticket(
        request=request,
        usecase="create",
        ticket_instance=ticket_instance,
        edit_url=edit_url,
        success_msg_tpl=success_msg_tpl,
    )


@login_required
def edit_ticket(request: HttpRequest, ticket_id: int) -> HttpResponse:
    """Edit an existing ticket"""
    ticket_instance = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    edit_url = urls.reverse("edit_ticket", kwargs={"ticket_id": ticket_id})
    success_msg_tpl = _("Updated ticket #%(ticket_id)i: %(ticket_title)s")
    return _edit_or_create_ticket(
        request=request,
        usecase="update",
        ticket_instance=ticket_instance,
        edit_url=edit_url,
        success_msg_tpl=success_msg_tpl,
    )


def _edit_or_create_ticket(
    request: HttpRequest,
    usecase: str,
    ticket_instance: Ticket,
    edit_url: str,
    success_msg_tpl: str,
):
    """Helper func to handle or display a form to edit or create a ticket.
    Edit and create a ticket follow a similar logic..."""
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
                return helpers.redirect_next(request, "feed")
    else:
        form = forms.EditTicketForm(instance=ticket_instance)
    context = {
        "usecase": usecase,
        "ticket_form": form,
        "ticket_id": ticket_instance.pk,
        "edit_url": helpers.add_next_url(edit_url, request),
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
    return helpers.redirect_next(request, "feed")


@login_required
def review_for_ticket(request: HttpRequest, ticket_id: int):
    """Creates a review in reply to a ticket.
    Ticket must be visible in the user's feed, otherwise the view will raise a 404.
    """
    ticket_instance = get_object_or_404(
        Ticket.with_user_manager,
        pk=ticket_id,
        user__in=subscription_tools.followed_users_or_self(user=request.user),
    )
    review_instance = Review(ticket=ticket_instance, user=request.user)
    return _edit_or_create_review(
        request=request,
        usecase="create",
        ticket_instance=ticket_instance,
        review_instance=review_instance,
        success_msg_tpl=_("You posted a new review in reply to ticket #%(ticket_id)d"),
        edit_url=urls.reverse("review_for_ticket", kwargs={"ticket_id": ticket_id}),
    )


@login_required
def edit_review(request: HttpRequest, review_id: int):
    """Updates an existing review."""
    review_instance = get_object_or_404(Review, pk=review_id, user=request.user)
    return _edit_or_create_review(
        request=request,
        usecase="update",
        ticket_instance=Ticket.with_user_manager.get(pk=review_instance.ticket_id),
        review_instance=review_instance,
        success_msg_tpl=_("Updated your review in reply to ticket #%(ticket_id)d"),
        edit_url=urls.reverse("edit_review", kwargs={"review_id": review_id}),
    )


def _edit_or_create_review(
    request: HttpRequest,
    usecase: str,
    ticket_instance: Ticket,
    review_instance: Review,
    success_msg_tpl: str,
    edit_url: str,
) -> HttpResponse:
    """Edit an exiting review, or create a new one in reply to an exiting ticket."""
    if request.POST.get("action") == "validate_review":
        form = forms.ReviewForm(request.POST, instance=review_instance)
        if form.is_valid():
            review: Review = form.save()
            messages.success(
                request, success_msg_tpl % ({"ticket_id": review.ticket.pk})
            )
            return helpers.redirect_next(request, "feed")
    else:
        form = forms.ReviewForm(instance=review_instance)
    context = {
        "review_form": form,
        "ticket": ticket_instance,
        "usecase": usecase,
        "edit_url": helpers.add_next_url(edit_url, request),
    }
    return render(request, "app/posts/edit_review.html", context)


@login_required
def create_review(request: HttpRequest):
    """Creates a review from scratch.
    POST data muts also contain the ticket data.
    Both ticket and review data must be valid to update the model.
    Redirect to user's feed on success.
    """
    if request.POST.get("action") == "validate_review":
        ticket_form = forms.EditTicketForm(
            request.POST, request.FILES, instance=Ticket(user=request.user)
        )
        review_form = forms.ReviewForm(request.POST, instance=Review(user=request.user))
        if ticket_form.is_valid() and review_form.is_valid():
            ticket_instance: Ticket = ticket_form.save()
            review_instance: Review = review_form.save(commit=False)
            review_instance.ticket = ticket_instance
            review_instance.save()
            messages.success(
                request,
                _("Created a new review for %(ticket_title)s")
                % ({"ticket_title": ticket_instance.title}),
            )
            return redirect("feed")
    else:
        ticket_form = forms.EditTicketForm(instance=Ticket(user=request.user))
        review_form = forms.ReviewForm(instance=Review(user=request.user))
    context = {
        "ticket_form": ticket_form,
        "review_form": review_form,
    }
    return render(request, "app/posts/create_review.html", context=context)


@login_required
def delete_review(request: HttpRequest, review_id: int):
    """Deletes a review written by the current user."""
    review_instance = get_object_or_404(Review, pk=review_id, user=request.user)
    review_instance.delete()
    messages.success(
        request,
        _("Deleted Review #%(review_id)d to ticket #%(ticket_id)d")
        % ({"review_id": review_id, "ticket_id": review_instance.ticket.pk}),
    )
    return helpers.redirect_next(request, "feed")


@login_required
def posts(request: HttpRequest) -> HttpResponse:
    """Display all reviews and tickets posted by a user."""
    # tickets = Ticket.objects.filter(user=request.user).select_related("user")
    tickets = Ticket.with_user_manager.from_user(request.user)
    reviews = (
        Review.objects.filter(user=request.user)
        .select_related("user")
        .select_related("ticket")
        .select_related("ticket__user")
    )
    posts = sorted(
        [
            post_tools.prepare_post_entry(
                post_obj=x, with_commands=True, next_url="posts", request=request
            )
            for x in chain(tickets, reviews)
        ],
        key=lambda x: x.time_created,
        reverse=True,
    )
    context = {"posts": posts, "display_commands": True}
    return render(request, "app/posts/posts.html", context=context)
