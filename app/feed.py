from .models import Ticket, Review, User, UserFollows
from django.db.models import QuerySet, Count


def feed_entries(user: User) -> list[dict]:
    """Returns a list of feed entries, sorted by date, descending.
    A feed entry is either a Review, or a Ticket requesting a review.

    An additional boolean can_review field is set to True if the current user can create
    a new review for a Ticket or an existing Review.
    """
    feed = []
    tickets = feed_tickets(user)

    for t in tickets:
        entry = {
            "type": "ticket",
            "ticket": t,
            "time_created": t.time_created,
            "can_review": t.num_reviews == 0
        }
        feed.append(entry)

    # for r in feed_reviews(user):
    # TODO: avoid N+1 queries when retrieving Ticket objects...
    for r in Review.objects.filter(ticket__in=tickets):
        entry = {
            "type": "review",
            "review": r,
            "time_created": r.time_created,
            "can_review": r.user != user,
        }
        feed.append(entry)
    feed.sort(key=lambda x: x['time_created'], reverse=True)
    return feed    


def feed_tickets(user: User) -> QuerySet[Ticket]:
    """Returns a collection of tickets
    """
    u_list = followed_users(user) + [user]
    # select_related on user to avoid N+1 problem when fecthing author details...
    tickets = Ticket.objects.annotate(num_reviews=Count("review")).filter(user__in=u_list).select_related("user")
    return tickets


def feed_reviews(user: User) -> QuerySet[Review]:
    """Returns a collection of reviews followed by the current user.
    """
    u_list = followed_users(user) + [user]
    # select_related on user to avoid N+1 problem when fecthing author details...
    return Review.objects.filter(user__in=u_list).select_related("user")


def followed_users(user: User) -> list[User]:
    """List users followed by the current user.
    """
    return [x.followed_user for x in UserFollows.objects.filter(user=user)]
