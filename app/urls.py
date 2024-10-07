from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('account/', include("my_auth.urls")),
    path("feed", views.feed, name="feed"),
    path("subscriptions", views.subscriptions, name="subscriptions"),
    path("subscriptions", views.subscriptions, name="add_subscription"),
    path("subscriptions/cancel/<int:followed_user_id>", views.subscription_cancel, name="cancel_subscription")
]
