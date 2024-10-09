from .models import Ticket, Review, User
from .posts import prepare_post_entry
from django.db.models import QuerySet, Count, Q
from .subscriptions import followed_users_or_self
from typing import Iterable
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def feed_entries(user: User) -> list[dict]:
    """Returns a list of feed entries, sorted by date, descending.
    A feed entry is a dict representing either a Review, or a Ticket requesting a review.

    See feed_post_dict() method for a list of available dict entries.
    """
    u_list = followed_users_or_self(user)
    # performance: reduce hits on DB by selecting related user and ticket objects.
    tickets = feed_tickets(user=user, following=u_list).select_related("user")
    reviews = feed_reviews(user=user, following=u_list).select_related("user").select_related("ticket")
    return chain_posts(tickets, reviews)


def chain_posts(tickets: Iterable[Ticket], reviews: Iterable[Review]) -> list[dict]:
    """Chains rleated reviews and tickets lists into a single ordered list of
    dictionnary, suitable to display in templates (for ex. in a user's feed).
    """
    ticket_posts_map = {x.pk: prepare_post_entry(x) for x in tickets}
    posts = list(ticket_posts_map.values())
    for r in reviews:
        review_post = prepare_post_entry(r)
        # performance hack: bind each review to the ticket we'v already fetched just before
        # so as to avoid N+1 queries when displaying a review and the requesting ticket.
        review_post['related_ticket'] = ticket_posts_map.get(r.ticket.pk)
        posts.append(review_post)
    posts.sort(
        key=lambda x: x.get("time_created"),
        reverse=True
    )
    return posts


def feed_tickets(user: User, following=None) -> QuerySet[Ticket]:
    """Returns a collection of tickets, annotated with the total number of reviews
    and the reviews posted by the user."""
    u_list = following or followed_users_or_self(user)
    own_reviews_q = Count("review", filter=Q(review__user=user))
    tickets = (
        Ticket.objects.annotate(total_reviews=Count("review"), own_reviews=own_reviews_q)
        .filter(user__in=u_list)
    )
    return tickets


def feed_reviews(user: User, following=None) -> QuerySet[Review]:
    """Returns a collection of reviews followed by the current user.
    This always includes reviews requested by the current user, regardless of the review's author.
    """
    u_list = following or followed_users_or_self(user)
    reviews = Review.objects.filter(user__in=u_list) | Review.objects.filter(ticket__user=user)
    return reviews
