from django.urls import path
from .views import GymCreateAPIView

urlpatterns = [
    path("", GymCreateAPIView.as_view(), name="gym-create"),
]