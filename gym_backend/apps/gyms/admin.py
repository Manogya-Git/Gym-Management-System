from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Gym, GymStaff


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "status", "currency", "created_at")
    list_display_links = ("id", "name")
    search_fields = ("name", "owner__email")
    list_filter = ("status", "currency")


@admin.register(GymStaff)
class GymStaffAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gym", "role", "is_active", "hired_on")
    list_display_links = ("id", "user")
    search_fields = ("user__email", "gym__name")
    list_filter = ("role", "is_active")