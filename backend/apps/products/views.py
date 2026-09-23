from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Product


def product_list(request):
    products = Product.objects.filter(is_available=True)

    query = request.GET.get("q", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
        )

    return render(
        request,
        "pages/products.html",
        {
            "products": products,
            "query": query,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_available=True,
    )

    return render(
        request,
        "pages/product_detail.html",
        {"product": product},
    )