from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.orders.models import Order
from .models import Payment


@login_required
def payment(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
    )

    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={
            "amount": order.total_price,
        },
    )

    return render(
        request,
        "pages/payment.html",
        {
            "order": order,
            "payment": payment,
        },
    )


@login_required
def process_payment(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
    )

    payment = get_object_or_404(
        Payment,
        order=order,
    )

    if request.method == "POST":
        payment.status = "paid"
        payment.ref_id = f"TEMP-{payment.id}"
        payment.save()

        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])

        return redirect(
            "orders:confirmation",
            order_id=order.id,
        )

    return redirect(
        "payments:payment",
        order_id=order.id,
    )