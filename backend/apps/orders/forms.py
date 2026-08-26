from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        label="Full name",
    )

    email = forms.EmailField(
        label="Email",
    )

    phone = forms.CharField(
        max_length=30,
        label="Phone",
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Address",
    )

    city = forms.CharField(
        max_length=100,
        label="City",
    )

    postal_code = forms.CharField(
        max_length=20,
        label="Postal code",
    )
