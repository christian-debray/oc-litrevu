from typing import Any
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from abc import abstractmethod
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Our custom User class
    see https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#auth-custom-user

    Additionnal fields:

    - *display_name*: Record the user name as it got entered during registration.
                Used for display only. *User.username* will store the lowercase version of the *display_name*.
    """
    display_name = models.CharField(
        max_length=150,
        null=False,
        verbose_name=_("username"),
        validators=[AbstractUser.username_validator],
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
    )

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.username
        super().save(*args, **kwargs)


class UserAwareManager(models.Manager):
    """Base class of user-aware managers.

    Provides filters on Post Entry ownership, relation between a user and Post Entry author, etc...
    """

    def get_queryset(self) -> models.QuerySet:
        """Select related user data, defers most unused user fields."""
        return (
            super()
            .get_queryset()
            .select_related("user")
            .defer(
                "user__password",
                "user__email",
                "user__first_name",
                "user__last_name",
                "user__is_staff",
                "user__is_active",
                "user__date_joined",
                "user__is_superuser",
                "user__last_login"
            )
        )

    def _followed_Q(self, user: User) -> models.Q:
        return models.Q(user__followed_by__user_id=user.pk)

    def own(self, user: User) -> models.QuerySet:
        """Filter: Instances posted by user."""
        return self.get_queryset().filter(user_id=user.pk)

    def followed(self, user: User) -> models.QuerySet:
        """Filter: Instances followed by user."""
        return self.get_queryset().filter(self._followed_Q(user))

    def own_or_followed(self, user: User) -> models.QuerySet:
        """Filter: Instances posted by user or followed by user."""
        own = models.Q(user_id=user.pk)
        return self.filter(own | self._followed_Q(user))


class TicketUserManager(UserAwareManager):
    """User-aware Ticket Manager.

    Annotates Ticket instances with:
      - total_reviews: the number of related reviews and the ticket author's name.

    Provides filters on ticket ownership, relation between a user and ticket author, etc...
    """

    def get_queryset(self):
        return super().get_queryset().annotate(
            total_reviews=models.Count("review")
        )


class ReviewUserManager(UserAwareManager):
    """A User-aware manager to query the Review model."""

    def get_queryset(self) -> models.QuerySet:
        return (
            super()
            .get_queryset()
            .select_related("ticket")
            .select_related("ticket__user")
        )

    def to_own_tickets(self, user: User) -> models.QuerySet:
        """Returns reviews related to user's tickets."""
        return self.get_queryset().filter(ticket__user_id=user.pk)

    def own_or_followed(self, user: User, filters=None) -> models.QuerySet:
        """Filter: Instances posted by user or followed by user. Also include all reviews to own's tickets."""
        own = models.Q(user_id=user.pk)
        followed = models.Q(user__followed_by__user_id=user.pk)
        to_own_tickets = models.Q(ticket__user_id=user.pk)
        q = self.filter(own | followed | to_own_tickets).distinct()
        if filters:
            return q.filter(filters)
        else:
            return q


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


class Ticket(AbstractPostEntry):
    """A user posts a ticket to request a review on an article or a book."""

    objects = models.Manager()
    with_user_manager = TicketUserManager()

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
    def review_url(self) -> str:
        return reverse("review_for_ticket", kwargs={"ticket_id": self.pk})

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


class PostEntry:
    """Proxy object to display tickets and reviews."""

    def __init__(self, model_instance: AbstractPostEntry, user: User):
        self.instance: AbstractPostEntry = model_instance
        self._visiting_user = user
        self._edit_url = None
        self._delete_url = None
        if model_instance.content_type == "REVIEW":
            self._ticket = PostEntry(model_instance.ticket, user)
        else:
            self._ticket = None
        self._commands: dict[dict] = {}

    def __getattr__(self, name: str):
        return getattr(self.instance, name)

    @property
    def ticket(self) -> "PostEntry":
        return self._ticket

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
    def can_review(self) -> bool:
        """True if the current user can create a review for this entry."""
        if self.content_type != "TICKET":
            return False
        else:
            return self.instance.total_reviews == 0

    @property
    def is_author(self) -> bool:
        """True if the current user is the author of this entry."""
        return self.instance.author_id == self._visiting_user.pk

    @property
    def commands(self) -> list[dict]:
        """A list of commands available for this Post."""
        return list(self._commands.values())

    def is_command_allowed(self, cmd_name):
        """Returns True if a command is available."""
        test_name = f"can_{cmd_name}"
        try:
            return getattr(self, test_name)
        except AttributeError:
            return False

    def set_command(self, cmd_name: str, **kwargs):
        """Sets the parameters for a command on this object, if the command is allowed.

        This method applies default options for each command.
        Command defaults can be overriden with the kwargs.

        Usual command options:
        - "url": (str)
        - "method": (str) "POST" or "GET"
        - "options": (dict)
        """
        if not self.is_command_allowed(cmd_name):
            return
        cmd_defaults = {}
        cmd_name = cmd_name.lower()
        match (cmd_name):
            case "edit":
                cmd_defaults = {"url": self.edit_url, "method": "GET", "options": {}}
            case "delete":
                cmd_defaults = {"url": self.delete_url, "method": "POST", "options": {}}
            case "review":
                cmd_defaults = {"url": self.review_url, "method": "GET", "options": {}}

        self._commands[cmd_name] = {"cmd_name": cmd_name} | cmd_defaults | kwargs

    def unset_command(self, cmd_name: str):
        """Removes a command from this object."""
        del self._commands[cmd_name]

    def __str__(self) -> str:
        return f"(PostEntry) {self.content_type} #{self.instance.pk} {self.instance}"
