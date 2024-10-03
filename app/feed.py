from .models import Ticket, Review, User
from django.db.models import QuerySet, Count, Q
from .subscriptions import followed_users


def feed_entries(user: User) -> list[dict]:
    """Returns a list of feed entries, sorted by date, descending.
    A feed entry is either a Review, or a Ticket requesting a review.

    An additional boolean can_review field is set to True if the current user can create
    a new review for a Ticket or an existing Review.
    """
    u_list = followed_users(user) | User.objects.filter(pk=user.pk)
    tickets = feed_tickets(user=user, following=u_list)
    reviews = feed_reviews(user=user, following=u_list)
    ticket_posts_map = {x.pk: feed_post_dict(x, "TICKET") for x in tickets}
    feed = list(ticket_posts_map.values())
    for r in reviews:
        review_post = feed_post_dict(r, "REVIEW")
        review_post['related_ticket'] = ticket_posts_map.get(r.ticket.pk)
        feed.append(review_post)
    feed.sort(
        key=lambda x: x.get("time_created"),
        reverse=True
    )
    return feed


def feed_post_dict(obj: Ticket | Review, content_type: str = None) -> dict:
    """Transform a review or a ticket into a standardized dict to use in templates."""
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
        post["image"] = obj.image
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
    u_list = following or (followed_users(user) | User.objects.filter(pk=user.pk))
    own_reviews_q = Count("review", filter=Q(review__user=user))
    tickets = (
        Ticket.objects.annotate(total_reviews=Count("review"), own_reviews=own_reviews_q)
        .filter(user__in=u_list)
        .select_related("user")
    )
    return tickets


def feed_reviews(user: User, following=None) -> QuerySet[Review]:
    """Returns a collection of reviews followed by the current user."""
    u_list = following or (followed_users(user) | User.objects.filter(pk=user.pk))
    # always include reviews related ot the user's own tickets
    reviews = Review.objects.filter(user__in=u_list) | Review.objects.filter(ticket__user=user)
    reviews = (
        Review.objects.filter(user__in=u_list)
        .union(Review.objects.filter(ticket__in=Ticket.objects.filter(user=user)))
    )
    return reviews
