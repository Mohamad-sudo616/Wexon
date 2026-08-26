from django.shortcuts import get_object_or_404, redirect, render

from apps.products.models import Product

from .models import Cart, CartItem


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(
        session_key=session_key,
        defaults={
            "user": request.user if request.user.is_authenticated else None
        },
    )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect("cart:detail")


def cart_detail(request):
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(
        session_key=session_key,
        defaults={
            "user": request.user if request.user.is_authenticated else None
        },
    )

    return render(
        request,
        "pages/cart_detail.html",
        {"cart": cart},
    )