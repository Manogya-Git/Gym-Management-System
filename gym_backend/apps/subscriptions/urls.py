from django.urls import path

from .views import (
    SubscriptionListCreateAPIView,
    SubscriptionDetailAPIView,
    SubscriptionCancelAPIView,
    SubscriptionRestoreAPIView,
    CancelledSubscriptionListAPIView,
)

urlpatterns = [
    path("", 
         SubscriptionListCreateAPIView.as_view(), 
         name="subscription-list-create"
    ),
    path(
        "<int:id>/",
        SubscriptionDetailAPIView.as_view(), 
        name="subscription-detail"
    ),
    path(
        "<int:id>/delete/",
        SubscriptionCancelAPIView.as_view(),
        name="subscription-cancel",
    ),
    path(
        "<int:pk>/restore/",
        SubscriptionRestoreAPIView.as_view(),
        name="subscription-restore",
    ),
    path(
    "cancelled/",
    CancelledSubscriptionListAPIView.as_view(),
    name="cancelled-subscriptions",
),
    
]
