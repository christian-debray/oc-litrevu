from .models import Ticket, User
from django.http import HttpRequest
from . import forms


def handle_ticket_form(form: forms.EditTicketForm) -> dict:
    """Handles a ticket form and returns a dictionnary of valid values."""
    if form.is_valid():
        form_data = {
            "title": form.cleaned_data.get("title"),
            "description": form.cleaned_data.get("description"),
            # todo: handle image files...
            "image": None,
        }
        return form_data
    return form


def create_ticket(request: HttpRequest, user: User, **ticket_data) -> Ticket:
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


def update_ticket(
    request: HttpRequest, user: User, ticket_id: int, **ticket_data
) -> Ticket:
    """Updates an existing Ticket and returns the updated Ticket object on success.
    Raises Ticket.DoesNotExist if ticket is not found or does not belong to user.
    """
    ticket_instance = Ticket.objects.get(user=user, pk=ticket_id)
    ticket_instance.title = ticket_data.get("title")
    ticket_instance.description = ticket_data.get("description")
    ticket_instance.save()
    return ticket_instance
