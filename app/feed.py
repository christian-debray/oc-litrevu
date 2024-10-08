from .models import Ticket, Review, User
from django.db.models import QuerySet, Count, Q
from .subscriptions import followed_users_or_self


def feed_entries(user: User) -> list[dict]:
    """Returns a list of feed entries, sorted by date, descending.
    A feed entry is a dict representing either a Review, or a Ticket requesting a review.

    See feed_post_dict() method for a list of available dict entries.
    """
    u_list = followed_users_or_self(user)
    # performance: reduce hits on DB by selecting related user and ticket objects.
    tickets = feed_tickets(user=user, following=u_list).select_related("user")
    reviews = feed_reviews(user=user, following=u_list).select_related("user").select_related("ticket")
    ticket_posts_map = {x.pk: feed_post_dict(x, "TICKET") for x in tickets}
    feed = list(ticket_posts_map.values())
    for r in reviews:
        review_post = feed_post_dict(r, "REVIEW")
        # performance hack: bind each review to the ticket we'v already fetched just before
        # so as to avoid N+1 queries when displaying a review and the requesting ticket.
        review_post['related_ticket'] = ticket_posts_map.get(r.ticket.pk)
        feed.append(review_post)
    feed.sort(
        key=lambda x: x.get("time_created"),
        reverse=True
    )
    return feed


def feed_post_dict(obj: Ticket | Review, content_type: str = None) -> dict:
    """Transform a review or a ticket into a standardized dict to use in templates.
    """
    content_type = content_type or ("TICKET" if isinstance(obj, Ticket) else "REVIEW")
    post = {
        "id": obj.pk,
        "type": content_type,
        "time_created": obj.time_created,
        "author_name": obj.user.username,
        "author_id": obj.user.pk
    }
    if content_type == "TICKET":
        post["title"] = obj.title
        post["body"] = obj.description
        post["image"] = obj.image.url if obj.image else None
        post["num_reviews"] = obj.total_reviews
        post["can_review"] = obj.own_reviews == 0
    elif content_type == "REVIEW":
        post["title"] = obj.headline
        post["body"] = obj.body
        post["rating"] = obj.rating
        post["ticket_id"] = obj.ticket.pk
    return post


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
