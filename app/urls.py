from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("auth", views.auth, name="auth"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
    path("feed", views.feed, name="feed"),
    path("subscriptions", views.subscriptions, name="subscriptions"),
    path("subscriptions", views.subscriptions, name="add_subscription"),
    path("subscriptions/cancel/<int:followed_user_id>", views.subscription_cancel, name="cancel_subscription")
]
