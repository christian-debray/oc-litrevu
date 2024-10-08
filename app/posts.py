from .models import Ticket, User
from . import forms
from django.contrib import messages
from django.http import HttpRequest
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger()

# def handle_ticket_form(form: forms.EditTicketForm) -> dict:
#     """Handles a ticket form and returns a dictionnary of valid values."""
#     if form.is_valid():
#         form_data = {
#             "title": form.cleaned_data.get("title"),
#             "description": form.cleaned_data.get("description"),
#             # todo: handle image files...
#             "image": None,
#         }
#         return form_data
#     return form


def handle_ticket_form(
    request: HttpRequest,
    form: forms.EditTicketForm,
    ticket_author: User,
    ticket_instance: Ticket = None,
) -> bool:
    """Handles a ticket form and returns True if the model was successfully updated.
    If the update failed, sets the form errors and returns false."""
    try:
        if form.is_valid():
            form_data = {
                "title": form.cleaned_data.get("title"),
                "description": form.cleaned_data.get("description"),
                # todo: handle image files...
                "image": None,
            }
            if ticket_instance:
                updated_ticket = update_ticket(user=ticket_author, ticket_instance=ticket_instance, **form_data)
                success_msg_tpl = _("Updated ticket #%(ticket_id)i: %(ticket_title)s")
            else:
                updated_ticket = create_ticket(user=ticket_author, **form_data)
                success_msg_tpl = _(
                    "Created a new ticket #%(ticket_id)i: %(ticket_title)s"
                )
            if updated_ticket:
                success_msg = success_msg_tpl % {
                    "ticket_id": updated_ticket.pk,
                    "ticket_title": updated_ticket.title,
                }
                messages.success(request, success_msg)
                return True
    except Exception as e:
        messages.error(request, _("Operation failed"))
        logger.error(e)
    return False


def create_ticket(user: User, **ticket_data) -> Ticket:
    """Creates and stores a new Ticket under a user's name with the data provided.
    Returns the new Ticket instance.
    """
    ticket_instance = Ticket.objects.create(
        user=user,
        title=ticket_data.get("title"),
        description=ticket_data.get("description"),
    )
    ticket_instance.save()
    return ticket_instance


def update_ticket(user: User, ticket_id: int = None, ticket_instance: Ticket = None,  **ticket_data) -> Ticket:
    """Updates an existing Ticket and returns the updated Ticket object on success.
    Accepts either a ticket_id or a ticket instance.

    Raises Ticket.DoesNotExist if ticket is not found or does not belong to user.
    """
    if not ticket_instance:
        ticket_instance = Ticket.objects.get(user=user, pk=ticket_id)
    elif ticket_instance.user.pk != user.pk:
        raise Ticket.DoesNotExist("Ticket does not belong to user")
    ticket_instance.title = ticket_data.get("title")
    ticket_instance.description = ticket_data.get("description")
    ticket_instance.save()
    return ticket_instance
