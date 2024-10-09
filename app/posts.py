"""Helpers to display posts entries in feeds
"""
from . import models as app_models
from django.urls import reverse


def get_command_uri(cmd_name, obj) -> str:
    """Returns the URI to execute a command on a post object (Ticket or Review).
    """
    if isinstance(obj, app_models.Ticket):
        return get_ticket_command_uri(cmd_name, obj)
    elif isinstance(obj, app_models.Review):
        return get_review_command_uri(cmd_name, obj)
    return None


def get_ticket_command_uri(cmd_name: str, ticket: app_models.Ticket) -> str:
    """Returns the URI to execute a command on a ticket.
    """
    match(cmd_name):
        case "edit":
            return reverse("edit_ticket", kwargs={"ticket_id": ticket.pk})
        case "delete":
            return reverse("delete_ticket", kwargs={"ticket_id": ticket.pk})
        case "review":
            return reverse("review_for_ticket", kwargs={"ticket_id": ticket.pk})
    return None


def get_review_command_uri(cmd_name: str, review: app_models.Review) -> str:
    """Returns the URI to execute a command on a review.
    """
    match(cmd_name):
        case "edit":
            return reverse("edit_review", kwargs={"review_id": review.pk})
        case "delete":
            return reverse("delete_review", kwargs={"review_id": review.pk})
    return None
