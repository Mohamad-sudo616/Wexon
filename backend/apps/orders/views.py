from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.models import Cart
from apps.payments.models import Payment
from apps.products.models import Product

from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)

    cart_items = list(
        cart.items.select_related("product")
    )

    if not cart_items:
        return redirect("cart:detail")

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    stock_error = None

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Lock products in a consistent order to reduce deadlocks.
                    product_ids = sorted({
                        item.product_id for item in cart_items
                    })

                    locked_products = {
                        product.id: product
                        for product in Product.objects.select_for_update()
                        .filter(id__in=product_ids)
                        .order_by("id")
                    }

                    # Recheck all items while the product rows are locked.
                    for item in cart_items:
                        product = locked_products.get(item.product_id)

                        if (
                            product is None
                            or not product.is_available
                            or product.stock < item.quantity
                        ):
                            raise ValueError(
                                f"Sorry, {item.product.name} does not have "
                                "enough stock to complete your order."
                            )

                    # Deduct stock atomically.
                    for item in cart_items:
                        updated = Product.objects.filter(
                            id=item.product_id,
                            is_available=True,
                            stock__gte=item.quantity,
                        ).update(stock=F("stock") - item.quantity)

                        if updated != 1:
                            raise ValueError(
                                f"Sorry, {item.product.name} does not have "
                                "enough stock to complete your order."
                            )

                    order = Order.objects.create(
                        user=request.user,
                        full_name=form.cleaned_data["full_name"],
                        email=form.cleaned_data["email"],
                        phone=form.cleaned_data["phone"],
                        address=form.cleaned_data["address"],
                        city=form.cleaned_data["city"],
                        postal_code=form.cleaned_data["postal_code"],
                        total_price=total,
                        stock_reserved=True,
                    )

                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=locked_products[item.product_id],
                            product_name=locked_products[item.product_id].name,
                            price=locked_products[item.product_id].price,
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

            except ValueError as exc:
                stock_error = str(exc)

    else:
        form = CheckoutForm()

        for item in cart_items:
            if (
                not item.product.is_available
                or item.product.stock < item.quantity
            ):
                stock_error = (
                    f"Sorry, {item.product.name} does not have enough stock "
                    "to complete your order."
                )
                break

    return render(
        request,
        "pages/checkout.html",
        {
            "form": form,
            "cart_items": cart_items,
            "total": total,
            "stock_error": stock_error,
        },
    )


@login_required
def confirmation(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
    )

    return render(
        request,
        "pages/order_confirmation.html",
        {"order": order},
    )
