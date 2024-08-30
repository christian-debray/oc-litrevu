from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Ticket, Review, UserFollows

admin.site.register(User, UserAdmin)
admin.site.register(Ticket)
admin.site.register(Review)
admin.site.register(UserFollows)
