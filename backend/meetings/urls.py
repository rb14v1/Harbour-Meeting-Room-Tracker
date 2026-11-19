from django.urls import path

from meetings import views

urlpatterns = [
    path("health", views.Health.as_view(), name="health"),
    path("dashboard", views.Dashboard.as_view(), name="dashboard"),
    path("rooms", views.RoomList.as_view(), name="rooms"),
    path("rooms/<int:pk>", views.RoomDetail.as_view(), name="room-detail"),
    path("availability", views.Availability.as_view(), name="availability"),
    path("bookings", views.BookingList.as_view(), name="bookings"),
    path("bookings/<int:pk>", views.BookingDetail.as_view(), name="booking-detail"),
    path("bookings/<int:pk>/cancel", views.BookingCancel.as_view(), name="booking-cancel"),
    path("reports/summary", views.ReportSummary.as_view(), name="reports"),
]
