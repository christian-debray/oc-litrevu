"""Helpers to display posts entries in feeds
"""

from .models import Ticket, Review
from django.urls import reverse
from . import helpers
from django.http import HttpRequest


def prepare_post_entry(
    post_obj: Review | Ticket,
    with_commands: bool = False,
    next_url: str = None,
    request: HttpRequest = None
) -> dict:
    """Renders all properties required to display a post entry.
    returns the result as a dictionnary.
    """
    post_dict = feed_post_dict(post_obj)
    if with_commands:
        commands = {}
        for cmd_name in post_obj.available_commands(request.user):
            commands[cmd_name] = helpers.add_next_url(
                request=request,
                url=get_command_uri(cmd_name, post_obj),
                next_url=next_url,
            )
        post_dict['commands'] = commands
    return post_dict


def feed_post_dict(obj: Ticket | Review, content_type: str = None, **kwargs) -> dict:
    """Transform a review or a ticket into a standardized dict to use in templates.
    Accepts optionnal keywords to override values in the resuting dictionnary.
    """
    content_type = content_type or ("TICKET" if isinstance(obj, Ticket) else "REVIEW")
    post = {
        "id": obj.pk,
        "type": content_type,
        "time_created": obj.time_created,
        "author_name": obj.user.username,
        "author_id": obj.user.pk,
    }
    if content_type == "TICKET":
        post["title"] = obj.title
        post["body"] = obj.description
        post["image"] = obj.image.url if obj.image else None
        post["num_reviews"] = obj.total_reviews if hasattr(obj, "total_reviews") else None
        post["can_review"] = obj.own_reviews == 0 if hasattr(obj, "own_reviews") else None
        post["ticket_id"] = obj.pk
    elif content_type == "REVIEW":
        post["title"] = obj.headline
        post["body"] = obj.body
        post["rating"] = obj.rating
        post["ticket_id"] = obj.ticket.pk
        # @todo N+1 DB hit
        post["related_ticket"] = feed_post_dict(obj.ticket, "TICKET", **kwargs)
    for k, v in kwargs.items():
        post[k] = v
    return post


def get_command_uri(cmd_name, obj) -> str:
    """Returns the URI to execute a command on a post object (Ticket or Review)."""
    if isinstance(obj, Ticket):
        return get_ticket_command_uri(cmd_name, obj)
    elif isinstance(obj, Review):
        return get_review_command_uri(cmd_name, obj)
    return None


def get_ticket_command_uri(cmd_name: str, ticket: Ticket) -> str:
    """Returns the URI to execute a command on a ticket."""
    match (cmd_name):
        case "edit":
            return reverse("edit_ticket", kwargs={"ticket_id": ticket.pk})
        case "delete":
            return reverse("delete_ticket", kwargs={"ticket_id": ticket.pk})
        case "review":
            return reverse("review_for_ticket", kwargs={"ticket_id": ticket.pk})
    return None


def get_review_command_uri(cmd_name: str, review: Review) -> str:
    """Returns the URI to execute a command on a review."""
    match (cmd_name):
        case "edit":
            return reverse("edit_review", kwargs={"review_id": review.pk})
        case "delete":
            return reverse("delete_review", kwargs={"review_id": review.pk})
    return None
