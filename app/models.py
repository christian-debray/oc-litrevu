from typing import Any
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username: str) -> Any:
        return self.get(username__iexact=username)


class User(AbstractUser):
    """Our custom User class
    see https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#auth-custom-user

    Custom behaviour: username is case-insensitive
    """
    objects = CustomUserManager()


class Ticket(models.Model):
    """A user posts a ticket to request a review on an article or a book."""
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(verbose_name=_("title"), max_length=128)
    description = models.TextField(
        verbose_name=_("description"), max_length=2048, blank=True
    )
    image = models.ImageField(
        null=True,
        verbose_name=_("image"),
        blank=True,
        upload_to="uploads/tickets/%Y/%m/%d/",
    )

    class Meta:
        verbose_name = _("ticket")
        verbose_name_plural = _("tickets")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._total_reviews: int = 0

    @property
    def content_type(self) -> str:
        return "TICKET"

    @property
    def edit_url(self) -> str:
        return reverse("edit_ticket", kwargs={"ticket_id": self.pk})

    @property
    def delete_url(self) -> str:
        return reverse("delete_ticket", kwargs={"ticket_id": self.pk})

    @property
    def total_reviews(self):
        """The number of reviews posted for this ticket."""
        return self._total_reviews

    @total_reviews.setter
    def total_reviews(self, value: int):
        """Sets the total number of reviews posted for this ticket.
        Most likely set by an annotation."""
        self._total_reviews = value

    @property
    def can_review(self) -> bool:
        return self.total_reviews == 0

    @property
    def review_url(self) -> str:
        return reverse("review_for_ticket", kwargs={"ticket_id": self.pk})

    def __str__(self):
        return self.title


class Review(models.Model):
    """A review replies to a ticket and rates and reviews an article or a book.
    We accept at most one review per ticket.
    """
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        verbose_name=_("rating"),
        # validates that rating must be between 0 and 5
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    headline = models.CharField(verbose_name=_("headline"), max_length=128)
    body = models.TextField(verbose_name=_("body"), max_length=8192, blank=True)

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")

    @property
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
