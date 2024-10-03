"""Toolbox to follow / drop other users"""
from .models import User, UserFollows
from django.db.models import QuerySet


def followed_users(user: User) -> QuerySet[User]:
    """Query users followed by the current user.
    """
    return User.objects.filter(followed_by__in=UserFollows.objects.filter(user=user))


def followers(user: User) -> QuerySet[User]:
    """Query users following the current user.
    """
    return User.objects.filter(following__in=UserFollows.objects.filter(followed_user=user))
