from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    return render(
        request,
        "pages/products.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "selected_category": category_slug,
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