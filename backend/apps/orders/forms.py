from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        label="Full name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your full name",
            }
        ),
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
            }
        ),
    )

    phone = forms.CharField(
        max_length=30,
        label="Phone",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your phone number",
            }
        ),
    )

    address = forms.CharField(
        label="Address",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter your full delivery address",
            }
        ),
    )

    city = forms.CharField(
        max_length=100,
        label="City",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your city",
            }
        ),
    )

    postal_code = forms.CharField(
        max_length=20,
        label="Postal code",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your postal code",
            }
        ),
    )