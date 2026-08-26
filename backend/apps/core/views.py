from django.contrib.auth import login
from django.shortcuts import redirect, render

from apps.products.models import Product

from .forms import RegistrationForm


def home(request):
    products = Product.objects.filter(is_available=True)

    context = {
        "products": products,
    }

    return render(request, "pages/home.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect("home")

    else:
        form = RegistrationForm()

    return render(
        request,
        "pages/register.html",
        {
            "form": form,
        },
    )