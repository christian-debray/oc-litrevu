"""Helpers to display posts entries in feeds
"""

from .models import Ticket, Review, AbstractPostEntry, PostEntry
from . import helpers
from django.http import HttpRequest


def prepare_post_entry(
    post_obj: Review | Ticket,
    with_commands: bool = False,
    next_url: str = None,
    request: HttpRequest = None
) -> AbstractPostEntry:
    """Sets all properties required to display a post entry.
    """
    entry = PostEntry(post_obj, request.user)

    if with_commands and post_obj.can_edit(request.user):
        entry.edit_url = helpers.add_next_url(
            request=request,
            url=post_obj.edit_url,
            next_url=next_url,
        )
    else:
        entry.edit_url = None
    if with_commands and post_obj.can_delete(request.user):
        entry.delete_url = helpers.add_next_url(
            request=request,
            url=post_obj.delete_url,
            next_url=next_url,
        )
    else:
        entry.delete_url = None
    return entry
