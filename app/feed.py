from .models import Ticket, Review, User, UserFollows
from django.db.models import QuerySet


def feed_entries(user: User):
    """Returns a list of feed entries, sorted by date, descending.
    A feed entry is either a Review, or a Ticket requesting a review.
    """
    feed = []
    for t in feed_tickets(user):
        entry = {
            "type": "ticket",
            "ticket": t,
            "time_created": t.time_created
        }
        feed.append(entry)

    for r in feed_reviews(user):
        entry = {
            "type": "review",
            "review": r,
            "time_created": r.time_created
        }
        feed.append(entry)
    feed.sort(key=lambda x: x['time_created'], reverse=True)
    return feed


def feed_tickets(user: User) -> QuerySet[Ticket]:
    """Returns a collection of tickets
    """
    u_list = followed_users(user) or []
    u_list.append(user)
    return Ticket.objects.filter(user__in=u_list).order_by("-time_created")


def feed_reviews(user: User) -> QuerySet[Review]:
    """Returns a collection of reviews
    """
    u_list = followed_users(user) or []
    u_list.append(user)
    return Review.objects.filter(user__in=u_list).order_by("-time_created")


def followed_users(user: User) -> list[User]:
    return [x.followed_user for x in UserFollows.objects.filter(user=user)]
