from django.urls import path

from . import views

urlpatterns = [
    path("login", views.auth, name="auth"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
]
