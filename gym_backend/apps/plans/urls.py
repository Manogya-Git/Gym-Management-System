from django.urls import path
from .views import (
    PlanListCreateAPIView,
    PlanDetailAPIView,
    PlanDeleteAPIView,
    InactivePlanListAPIView,
    PlanRestoreAPIView,
)

urlpatterns = [
    path("", PlanListCreateAPIView.as_view(), name="plan-list-create"),
    path("<int:id>/", PlanDetailAPIView.as_view(), name="plan-detail"),
    path("<int:id>/delete/", PlanDeleteAPIView.as_view(), name="plan-delete"),
    path("inactive/", InactivePlanListAPIView.as_view(), name="inactive-plans"),
    path("<int:id>/restore/", PlanRestoreAPIView.as_view(), name="plan-restore"),
]