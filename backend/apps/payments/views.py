import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.orders.models import Order
from .models import Payment

ZARINPAL_REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_STARTPAY_URL = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"


@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={"amount": order.total_price},
    )

    return render(
        request,
        "pages/payment.html",
        {"order": order, "payment": payment},
    )


@login_required
def process_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = get_object_or_404(Payment, order=order)

    if request.method != "POST":
        return redirect("payments:payment", order_id=order.id)

    if order.status != "pending" or payment.status == "paid":
        return redirect("payments:payment", order_id=order.id)

    callback_url = request.build_absolute_uri(
        reverse("payments:verify", args=[order.id])
    )

    data = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(payment.amount),
        "description": f"Payment for order #{order.id}",
        "callback_url": callback_url,
    }

    try:
        res = requests.post(ZARINPAL_REQUEST_URL, json=data, timeout=10)
        result = res.json()
    except (requests.RequestException, ValueError):
        return redirect("payments:payment_failed", order_id=order.id)

    if "data" in result and result["data"].get("code") == 100:
        authority = result["data"]["authority"]
        payment.authority = authority
        payment.save(update_fields=["authority", "updated_at"])

        return redirect(ZARINPAL_STARTPAY_URL.format(authority=authority))

    return redirect("payments:payment_failed", order_id=order.id)


@login_required
def verify_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = get_object_or_404(Payment, order=order)

    # A verified payment must never be processed twice.
    if payment.status == "paid" and order.status == "paid":
        return redirect("orders:confirmation", order_id=order.id)

    authority = request.GET.get("Authority")
    status_param = request.GET.get("Status")

    if not authority or authority != payment.authority:
        return redirect("payments:payment_failed", order_id=order.id)

    if status_param != "OK":
        payment.status = "failed"
        payment.save(update_fields=["status", "updated_at"])
        return redirect("payments:payment_failed", order_id=order.id)

    verify_data = {
        "merchant_id": settings.ZARINPAL_MERCHANT_ID,
        "amount": int(payment.amount),
        "authority": authority,
    }

    try:
        res = requests.post(ZARINPAL_VERIFY_URL, json=verify_data, timeout=10)
        result = res.json()
    except (requests.RequestException, ValueError):
        return redirect("payments:payment_failed", order_id=order.id)

    if "data" in result and result["data"].get("code") in (100, 101):
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)
            locked_order = Order.objects.select_for_update().get(pk=order.pk)

            if locked_payment.status != "paid":
                locked_payment.status = "paid"
                locked_payment.ref_id = result["data"].get("ref_id") or ""
                locked_payment.save(
                    update_fields=["status", "ref_id", "updated_at"]
                )

                locked_order.status = "paid"
                locked_order.save(update_fields=["status", "updated_at"])

        return redirect("orders:confirmation", order_id=order.id)

    payment.status = "failed"
    payment.save(update_fields=["status", "updated_at"])
    return redirect("payments:payment_failed", order_id=order.id)


@login_required
def payment_failed(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = get_object_or_404(Payment, order=order)

    return render(
        request,
        "pages/payment_failed.html",
        {"order": order, "payment": payment},
    )