from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from abc import abstractmethod
from django.urls import reverse


class User(AbstractUser):
    """Our custom User class
    see https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#auth-custom-user
    """


class AbstractPostEntry(models.Model):
    """Interface to all post entries: Tickets and Reviews"""

    class Meta:
        abstract = True

    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Returns a strign describing the entry's content type"""
        pass

    def can_edit(self, user: User, **kwargs) -> bool:
        """Returns True if this instance can be edited in a given context."""
        return user is not None and user.pk == self.user_id

    def can_delete(self, user: User, **kwargs) -> bool:
        """Returns True if this instance can be deleted in a given context."""
        return user is not None and user.pk == self.user_id


class Ticket(AbstractPostEntry):
    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    image = models.ImageField(
        null=True, blank=True, upload_to="uploads/tickets/%Y/%m/%d/"
    )

    @property
    def content_type(self):
        return "TICKET"

    @property
    def edit_url(self) -> str:
        return reverse("edit_ticket", kwargs={"ticket_id": self.pk})

    @property
    def delete_url(self) -> str:
        return reverse("delete_ticket", kwargs={"ticket_id": self.pk})

    def __str__(self):
        return self.title


class Review(AbstractPostEntry):
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        # validates that rating must be between 0 and 5
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)

    @property
    def content_type(self):
        return "REVIEW"

    @property
    def edit_url(self) -> str:
        return reverse("edit_review", kwargs={"review_id": self.pk})

    @property
    def delete_url(self) -> str:
        return reverse("delete_review", kwargs={"review_id": self.pk})


class UserFollows(models.Model):
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


class PostEntry:
    """Proxy object to display tickets and reviews in feeds
    """
    def __init__(self, model_instance: Review | Ticket, user: User):
        self.instance: Review | Ticket = model_instance
        self.user = user
        self._edit_url = None
        self._delete_url = None

    def __getattr__(self, name: str):
        return getattr(self.instance, name)

    @property
    def delete_url(self):
        if self.instance.can_delete(self.user):
            return self._delete_url or self.instance.delete_url
        else:
            return None

    @delete_url.setter
    def delete_url(self, val):
        if self.instance.can_delete(self.user):
            self._delete_url = val

    @property
    def edit_url(self):
        if self.instance.can_edit(self.user):
            return self._edit_url or self.instance.edit_url
        else:
            return None

    @edit_url.setter
    def edit_url(self, val):
        if self.instance.can_edit(self.user):
            self._edit_url = val
