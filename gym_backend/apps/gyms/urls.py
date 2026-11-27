from django.urls import path

from .views import (
    GymDetailAPIView,
    GymListCreateAPIView,
    GymStaffDetailAPIView,
    GymStaffListCreateAPIView,
)

urlpatterns = [
    path("", GymListCreateAPIView.as_view(), name="gym-list-create"),
    path("<int:id>/", GymDetailAPIView.as_view(), name="gym-detail"),
    path(
        "<int:gym_id>/staff/",
        GymStaffListCreateAPIView.as_view(),
        name="gym-staff-list-create",
    ),
    path(
        "<int:gym_id>/staff/<int:id>/",
        GymStaffDetailAPIView.as_view(),
        name="gym-staff-detail",
    ),
]
