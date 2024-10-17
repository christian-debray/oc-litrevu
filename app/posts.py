"""Helpers to display posts entries in feeds
"""

from .models import Ticket, Review, PostEntry
from django.http import HttpRequest


def prepare_post_entry(
    post_obj: Review | Ticket,
    request: HttpRequest,
    with_commands: list = None,
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

    To set commands on a post entry, pass a dictionnary with the with_commands parameter.
    Note: The entry's ID is implicit and is not required in the command options.

    commands param example :
    commands = [
        # pass a dict to set edit command with custom parameters:
        {'cmd_name': 'edit', 'cmd_url': "url/path/to/cmd", 'method': "GET", 'options': {'foo': 42, 'bar': "yellow"}},
        # apply defaults:
        {'cmd_name: 'review'},
        # just pass a string to set delete command with default parameters:
        "delete", # use the object default parameters
    ]
    """
    entry = PostEntry(post_obj, request.user)
    if with_commands and len(with_commands):
        for cmd in with_commands:
            if isinstance(cmd, str):
                args = {"cmd_name": cmd}
            else:
                args = cmd
            entry.set_command(**args)
    return entry
