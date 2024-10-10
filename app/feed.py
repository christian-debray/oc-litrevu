from .models import Ticket, Review, User
from django.db.models import QuerySet, Count
from .subscriptions import followed_users_or_self
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def feed_tickets(user: User, following=None) -> QuerySet[Ticket]:
    """Returns a collection of tickets, annotated with the total number of reviews
    and the reviews posted by the user."""
    u_list = following or followed_users_or_self(user)
    tickets = (
        Ticket.objects.filter(user__in=u_list)
        .annotate(total_reviews=Count("review"))
        .select_related("user")
    )
    return tickets


def feed_reviews(user: User, following=None) -> QuerySet[Review]:
    """Returns a collection of reviews followed by the current user.
    This always includes reviews requested by the current user, regardless of the review's author.
    """
    u_list = following or followed_users_or_self(user)
    reviews = (
        Review.objects.filter(user__in=u_list)
        .select_related("user")
        .select_related("ticket")
        .select_related("ticket__user")
    )
    return reviews
