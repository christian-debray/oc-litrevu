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
    path("posts/tickets/update", views.edit_ticket, name="update_ticket")
]
