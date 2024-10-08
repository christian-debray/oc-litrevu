from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('account/', include("my_auth.urls")),
    path("feed", views.feed, name="feed"),
    path("subscriptions", views.subscriptions, name="subscriptions"),
    path("subscriptions", views.subscriptions, name="add_subscription"),
    path("subscriptions/cancel/<int:followed_user_id>", views.subscription_cancel, name="cancel_subscription"),
    path("posts/tickets/new", views.edit_ticket, name="new_ticket"),
    path("posts/tickets/edit/<int:ticket_id>", views.edit_ticket, name="edit_ticket"),
    path("posts/tickets/update", views.edit_ticket, name="update_ticket"),
    path("posts/tickets/delete/<int:ticket_id>", views.delete_ticket, name="delete_ticket"),
    path("posts/review/for_ticket/<int:ticket_id>", views.review_for_ticket, name="review_for_ticket"),
    path("posts/review/create_review", views.create_review, name="create_review"),
    path("posts/review/edit/<int:review_id>", views.edit_review, name="edit_review")
]
