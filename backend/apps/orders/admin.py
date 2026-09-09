from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name",
        "price",
        "quantity",
        "item_subtotal",
    )

    @admin.display(description="Subtotal")
    def item_subtotal(self, obj):
        if not obj.price or not obj.quantity:
            return 0

        return obj.price * obj.quantity


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

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
    )

    readonly_fields = (
        "total_price",
        "created_at",
        "updated_at",
    )

    inlines = [OrderItemInline]