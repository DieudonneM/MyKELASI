from django.urls import path

from .views import BookingActionView, BookingCreateView, BookingDetailView, BookingListView

app_name = "bookings"

urlpatterns = [
    path("", BookingListView.as_view(), name="list"),
    path("nouvelle/<uuid:proposal_id>/", BookingCreateView.as_view(), name="create"),
    path("<uuid:public_id>/", BookingDetailView.as_view(), name="detail"),
    path("<uuid:public_id>/<str:action>/", BookingActionView.as_view(), name="action"),
]
