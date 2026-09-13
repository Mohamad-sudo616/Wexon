import requests

from django.conf import settings
from django.contrib.auth.decorators import login_required
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
    except requests.RequestException:
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

    authority = request.GET.get("Authority")
    status_param = request.GET.get("Status")

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
    except requests.RequestException:
        payment.status = "failed"
        payment.save(update_fields=["status", "updated_at"])
        return redirect("payments:payment_failed", order_id=order.id)

    if "data" in result and result["data"].get("code") in (100, 101):
        payment.status = "paid"
        payment.ref_id = result["data"].get("ref_id")
        payment.save()

        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])

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