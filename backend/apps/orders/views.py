from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.payments.models import Payment
from apps.cart.models import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    cart_items = cart.items.select_related("product")

    if not cart_items.exists():
        return redirect("cart:detail")

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            order = Order.objects.create(
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                address=form.cleaned_data["address"],
                city=form.cleaned_data["city"],
                postal_code=form.cleaned_data["postal_code"],
                total_price=total,
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity,
                )

            Payment.objects.create(
            order=order,
            amount=order.total_price,
        )

        cart.items.all().delete()

        return redirect(
            "payments:payment",
            order_id=order.id,
        )

    else:
        form = CheckoutForm()

    return render(
        request,
        "pages/checkout.html",
        {
            "form": form,
            "cart_items": cart_items,
            "total": total,
        },
    )


@login_required
def confirmation(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
    )

    return render(
        request,
        "pages/order_confirmation.html",
        {
            "order": order,
        },
    )