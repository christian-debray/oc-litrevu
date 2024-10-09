from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from abc import abstractmethod


class User(AbstractUser):
    """Our custom User class
    see https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#auth-custom-user
    """


class AbstractPostEntry:
    """Interface to all post entries: Tickets and Reviews"""

    def available_commands(self, user: User, **kwargs) -> list[str]:
        """Returns a list of command names available for this instance
        to a particular user.
        """
        commands = []
        if self.can_edit(user):
            commands.append("edit")
        if self.can_delete(user):
            commands.append("delete")
        return commands

    def can_edit(self, user: User, **kwargs) -> bool:
        """Returns True if this instance can be edited in a given context."""
        return user is not None and user.pk == self.author_id()

    def can_delete(self, user: User, **kwargs) -> bool:
        """Returns True if this instance can be deleted in a given context."""
        return user is not None and user.pk == self.author_id()

    @abstractmethod
    def author_id(self) -> int:
        """Returns the id of the user who posted this entry."""
        pass


class Ticket(models.Model, AbstractPostEntry):
    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(
        null=True, blank=True, upload_to="uploads/tickets/%Y/%m/%d/"
    )
    time_created = models.DateTimeField(auto_now_add=True)

    def author_id(self) -> int:
        return self.user_id

    def __str__(self):
        return self.title


class Review(models.Model, AbstractPostEntry):
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        # validates that rating must be between 0 and 5
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def author_id(self) -> int:
        return self.user_id


class UserFollows(models.Model):
    # Your UserFollows model definition goes here

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    followed_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followed_by",
    )

    class Meta:
        # ensures we don't get multiple UserFollows instances
        # for unique user-user_followed pairs
        unique_together = ("user", "followed_user")
