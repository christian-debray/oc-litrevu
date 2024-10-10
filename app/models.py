from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from abc import abstractmethod


class User(AbstractUser):
    """Our custom User class
    see https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#auth-custom-user
    """


class AbstractPostEntry(models.Model):
    """Interface to all post entries: Tickets and Reviews."""

    class Meta:
        abstract = True

    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    @property
    @abstractmethod
    def content_type(self) -> str:
        """A string describing the instance's content type."""
        pass

    @property
    @abstractmethod
    def edit_url(self) -> str:
        """Default string to edit/update a particular instance of this model."""
        pass

    @property
    @abstractmethod
    def delete_url(self) -> str:
        """Default string to delete a particular instance of this model."""
        pass

    @property
    def author_id(self) -> int:
        """ID of the author of this model's instance."""
        return self.user_id


class UserManager(models.Manager):
    """Base class of user-aware managers.

    Provides filters on Post Entry ownership, relation between a user and Post Entry author, etc...
    """

    def own(self, user: User):
        """Filter: Instances posted by user.
        """
        return self.get_queryset().filter(user=user)

    def followed(self, user: User):
        """Filter: Instances followed by user.
        """
        return self.get_queryset().filter(user__followed_by__user_id=user.pk)

    def own_or_followed(self, user: User):
        """Filter: Union of followed_by_user and from_user filters.
        """
        return self.own(user) | self.followed(user)


class TicketUserManager(UserManager):
    """User-aware Ticket Manager.

    Annotates Ticket instances with:
      - total_reviews: the number of related reviews and the ticket author's name.

    Provides filters on ticket ownership, relation between a user and ticket author, etc...
    """
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("user")
            .annotate(total_reviews=models.Count("review"))
            .only("pk", "user_id", "title", "image", "description", "time_created")
        )


class ReviewUserManager(UserManager):
    """A User-aware manager to query the Review model.
    """
    def get_queryset(self) -> models.QuerySet:
        return (
            super().get_queryset()
            .select_related("user")
            .select_related("ticket")
            .select_related("ticket__user")
        )


class Ticket(AbstractPostEntry):
    """A user posts a ticket to request a review on an article or a book."""

    objects = models.Manager()
    with_user_manager = TicketUserManager()

    title = models.CharField(max_length=128)
    description = models.TextField(max_length=2048, blank=True)
    image = models.ImageField(
        null=True, blank=True, upload_to="uploads/tickets/%Y/%m/%d/"
    )

    def content_type(self) -> str:
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
    """A review replies to a ticket and rates and reviews an article or a book.
    We accept at most one review per ticket.
    """

    objects = models.Manager()
    with_user_manager = ReviewUserManager()

    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        # validates that rating must be between 0 and 5
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    headline = models.CharField(max_length=128)
    body = models.TextField(max_length=8192, blank=True)

    def content_type(self) -> str:
        return "REVIEW"

    @property
    def edit_url(self) -> str:
        return reverse("edit_review", kwargs={"review_id": self.pk})

    @property
    def delete_url(self) -> str:
        return reverse("delete_review", kwargs={"review_id": self.pk})

    def __str__(self) -> str:
        return self.headline


class UserFollows(models.Model):
    """Follow Relationship between users."""

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
    """Proxy object to display tickets and reviews.
    """

    def __init__(self, model_instance: AbstractPostEntry, user: User):
        self.instance: AbstractPostEntry = model_instance
        self.user = user
        self._edit_url = None
        self._delete_url = None

    def __getattr__(self, name: str):
        return getattr(self.instance, name)

    @property
    def content_type(self) -> str:
        """A string representing the entry's type: REVIEW or TICKET."""
        return self.instance.content_type

    @property
    def delete_url(self):
        """The URL where the current user can edit this entry,
        or None if the current user can't edit the entry.
        """
        if self.can_delete:
            return self._delete_url or self.instance.delete_url
        else:
            return None

    @delete_url.setter
    def delete_url(self, val):
        if self.can_delete:
            self._delete_url = val

    @property
    def edit_url(self):
        """The URL where the current user can edit this entry,
        or None if the current user can't edit the entry.
        """
        if self.can_edit:
            return self._edit_url or self.instance.edit_url
        else:
            return None

    @edit_url.setter
    def edit_url(self, val):
        if self.can_edit:
            self._edit_url = val

    @property
    def can_edit(self) -> bool:
        """True if the current user can edit this entry."""
        return self.is_author

    @property
    def can_delete(self) -> bool:
        """True if the current user can delete this entry."""
        return self.is_author

    @property
    def is_author(self) -> bool:
        """True if the current user is the author of this entry."""
        return self.instance.author_id == self.user.pk
