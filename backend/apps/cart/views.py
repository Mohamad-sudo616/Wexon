from django.shortcuts import get_object_or_404, redirect, render

from apps.products.models import Product

from .models import Cart, CartItem


def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
        )
    else:
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
        )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
    )

    if created:
        if product.stock <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = 1
            cart_item.save()

    else:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()

    return redirect("cart:detail")

def update_cart_item(request, item_id):
    if request.user.is_authenticated:
        cart = get_object_or_404(
            Cart,
            user=request.user,
        )
    else:
        if not request.session.session_key:
            request.session.create()

        cart = get_object_or_404(
            Cart,
            session_key=request.session.session_key,
        )

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart,
    )

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1

        if quantity <= 0:
            cart_item.delete()

        elif quantity <= cart_item.product.stock:
            cart_item.quantity = quantity
            cart_item.save(update_fields=["quantity"])

        else:
            cart_item.quantity = cart_item.product.stock
            cart_item.save(update_fields=["quantity"])

    return redirect("cart:detail")


def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        cart = get_object_or_404(
            Cart,
            user=request.user,
        )
    else:
        if not request.session.session_key:
            request.session.create()

        cart = get_object_or_404(
            Cart,
            session_key=request.session.session_key,
        )

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart,
    )

    if request.method == "POST":
        cart_item.delete()

    return redirect("cart:detail")

def cart_detail(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
        )
    else:
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
        )

    cart_total = sum(
        item.total_price
        for item in cart.items.select_related("product")
    )

    return render(
        request,
        "pages/cart_detail.html",
        {
            "cart": cart,
            "cart_total": cart_total,
        },
    )