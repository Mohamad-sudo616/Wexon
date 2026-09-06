from django.urls import path

from . import views


app_name = "payments"


urlpatterns = [
    path(
        "<int:order_id>/",
        views.payment,
        name="payment",
    ),
    path(
        "<int:order_id>/process/",
        views.process_payment,
        name="process_payment",
    ),
]









