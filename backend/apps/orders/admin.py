from django.contrib import admin
from django.db import transaction
from django.db.models import F, Sum

from apps.products.models import Product
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("product", "quantity", "price", "item_subtotal")
    readonly_fields = ("item_subtotal",)

    @admin.display(description="Subtotal")
    def item_subtotal(self, obj):
        if not obj.pk or obj.price is None:
            return "-"
        return obj.subtotal


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "total_price",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = (
        "total_price",
        "stock_reserved",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            previous_order = None

            if change:
                previous_order = (
                    Order.objects.select_for_update().get(pk=obj.pk)
                )

            # Only restock when an unpaid order is cancelled.
            if (
                previous_order is not None
                and previous_order.status != "cancelled"
                and obj.status == "cancelled"
                and previous_order.status == "pending"
                and previous_order.stock_reserved
            ):
                quantities = list(
                    previous_order.items.values("product_id")
                    .annotate(total_quantity=Sum("quantity"))
                    .order_by("product_id")
                )

                product_ids = [
                    item["product_id"] for item in quantities
                ]

                # Lock products in a consistent order.
                list(
                    Product.objects.select_for_update()
                    .filter(id__in=product_ids)
                    .order_by("id")
                )

                for item in quantities:
                    Product.objects.filter(
                        id=item["product_id"]
                    ).update(
                        stock=F("stock") + item["total_quantity"]
                    )

                obj.stock_reserved = False

            super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        order = form.instance
        total = sum(item.subtotal for item in order.items.all())
        order.total_price = total
        order.save(update_fields=["total_price", "updated_at"])
