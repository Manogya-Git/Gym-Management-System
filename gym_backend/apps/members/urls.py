from django.urls import path
from .views import (
    DeletedMemberListAPIView,
    MemberCreateAPIView, 
    MemberDetailAPIView,
    MemberDeleteAPIView,
    MemberRestoreAPIView,
)

urlpatterns = [
    path("", MemberCreateAPIView.as_view(), name="member-create"),
    path("<int:id>/", MemberDetailAPIView.as_view(), name="member-detail"),
    path("<int:id>/delete/", MemberDeleteAPIView.as_view(), name="member-delete"),
    path("deleted/", DeletedMemberListAPIView.as_view(), name="deleted-members"),
    path("<int:id>/restore/", MemberRestoreAPIView.as_view(), name="member-restore"),
]