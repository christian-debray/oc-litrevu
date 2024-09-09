from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("auth", views.auth, name="auth"),
    path("register", views.register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("feed/", views.feed, name="feed")
]
