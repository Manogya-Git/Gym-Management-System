from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Gym, GymStaff


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "currency", "created_at")
    search_fields = ("name", "owner__email")
    list_filter = ("status", "currency")


@admin.register(GymStaff)
class GymStaffAdmin(admin.ModelAdmin):
    list_display = ("user", "gym", "role", "is_active", "hired_on")
    search_fields = ("user__email", "gym__name")
    list_filter = ("role", "is_active")