"""Toolbox to follow / drop other users"""
from .models import User, UserFollows
from django.db.models import QuerySet


def followed_users(user: User) -> QuerySet[User]:
    """Query users followed by the current user.
    """
    return User.objects.filter(followed_by__user_id=user.pk)


def followers(user: User) -> QuerySet[User]:
    """Query users following the current user.
    """
    return User.objects.filter(following__followed_user=user.pk)


def subscribe_to_user(user: User, follow_username: str) -> User:
    """Try to follow another user.

    - follow_username must be the exact username of a user not already followed.
    - Raises DoesNotExist if the user to follow is not found.

    Returns the followed user if successful.
    """
    not_followed = User.objects.exclude(followed_by__user=user).exclude(pk=user.pk)
    follow_user = not_followed.get(username=follow_username)
    follow = UserFollows.objects.create(user=user, followed_user=follow_user)
    follow.save()
    return follow_user


def cancel_subscription(user: User, followed_user_id: int):
    """Cancel a subscirption to a user's posts.

    - Raises DoesNotExist if no susbcription to user was found.
    """
    followed = UserFollows.objects.get(user=user, followed_user=followed_user_id)
    return followed.delete()
