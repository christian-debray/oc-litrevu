"""Helpers to display posts entries in feeds
"""

from .models import Ticket, Review, User
from django.db.models import QuerySet, Q, Count


def own_or_followed_reviews(user: User) -> QuerySet[Review]:
    """Finds reviews to display in a user's feed:
    owned by user, followed by user, or posted in reply to a ticket owned by user.
    """
    own = Q(user_id=user.pk)
    followed = Q(user__followed_by__user_id=user.pk)
    to_own_tickets = Q(ticket__user_id=user.pk)
    return (
        Review.objects.select_related("user")
        .select_related("ticket")
        .select_related("ticket__user")
        .filter(own | followed | to_own_tickets)
        .distinct()
    )


def own_or_followed_tickets(user: User) -> QuerySet[Ticket]:
    """Find tickets own ofr followed by user."""
    followed = Q(user__followed_by__user_id=user.pk)
    own = Q(user_id=user.pk)
    return Ticket.objects.select_related("user").filter(followed | own).annotate(total_reviews=Count("review"))


def prepare_post_entry(entry: Review | Ticket, with_commands: list = None) -> dict:
    """Serialize a Review or Ticket as a dictionnary. Related objects are serialized as well.

    Optionnaly set commands allowed for this entry.
    """
    entry_dict = {}
    if entry.content_type == "TICKET":
        entry_dict = ticket_dict(entry)
    elif entry.content_type == "REVIEW":
        entry_dict = review_dict(entry)
    else:
        return {}
    if with_commands:
        entry_dict["commands"] = []
        for cmd in with_commands:
            args = {"cmd_name": cmd} if isinstance(cmd, str) else cmd
            entry_dict["commands"].append(make_command(entry, **args))
    return entry_dict


def make_command(entry, cmd_name: str, **kwargs):
    """Sets the parameters for a command on this object, if the command is allowed.

    This method applies default options for each command.
    Command defaults can be overriden with the kwargs.

    Usual command options:
    - "url": (str)
    - "method": (str) "POST" or "GET"
    - "options": (dict)
    """
    cmd_defaults = {}
    cmd_name = cmd_name.lower()
    match (cmd_name):
        case "edit":
            cmd_defaults = {"url": entry.edit_url, "method": "GET", "options": {}}
        case "delete":
            cmd_defaults = {"url": entry.delete_url, "method": "POST", "options": {}}
        case "review":
            cmd_defaults = {"url": entry.review_url, "method": "GET", "options": {}}

    return {"cmd_name": cmd_name} | cmd_defaults | kwargs


def user_dict(obj: User) -> dict:
    return {
        "id": obj.pk,
        "username": obj.username,
    }


def ticket_dict(obj: Ticket) -> dict:
    return {
        "id": obj.pk,
        "content_type": obj.content_type,
        "user": user_dict(obj.user),
        "title": obj.title,
        "description": obj.description,
        "image": obj.image,
        "time_created": obj.time_created,
    }


def review_dict(obj: Review) -> dict:
    return {
        "content_type": obj.content_type,
        "user": user_dict(obj.user),
        "id": obj.pk,
        "rating": obj.rating,
        "title": obj.headline,
        "headline": obj.headline,
        "body": obj.body,
        "time_created": obj.time_created,
        "ticket": ticket_dict(obj.ticket),
    }
