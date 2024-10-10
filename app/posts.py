"""Helpers to display posts entries in feeds
"""

from .models import Ticket, Review, PostEntry
from . import helpers
from django.http import HttpRequest


def prepare_post_entry(
    post_obj: Review | Ticket,
    request: HttpRequest,
    with_commands: bool = False,
    next_url: str = None,
) -> PostEntry:
    """Helper to convert a Review or Ticket instance into a PostEntry proxy object (see models).

    Use it if you need to control the urls to edit and delete a Post Entry.

    params:
        - post_obj: a Review or Ticket instance
        - request: the current request object.
            This function will use request.user to produce a PostEntry instance
            and will aslo read the current query string if a url transformation is required (see below)
        - with_commands: True if edit_url and delete_url are needed.
            False will set both urls to None.
        - next_url: if set, transforms the instance' edit_url and delete_url by adding a "next" query parameter,
            to help control execution flow and redirections after a successful command.
    """
    entry = PostEntry(post_obj, request.user)

    # no url transform required:
    if not with_commands or not next_url:
        entry.edit_url = None
        entry.delete_url = None
        return entry

    # transform the entry's urls:
    if entry.can_edit:
        entry.edit_url = helpers.add_next_url(request=request, url=post_obj.edit_url, next_url=next_url)
    if entry.can_delete:
        entry.delete_url = helpers.add_next_url(request=request, url=post_obj.delete_url, next_url=next_url)

    return entry
