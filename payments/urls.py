from django.urls import path

from .views import ChargeView

urlpatterns = [
    path("charge", ChargeView.as_view(), name="charge"),
]
