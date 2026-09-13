from django.contrib import admin

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

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        order = form.instance
        total = sum(item.subtotal for item in order.items.all())
        order.total_price = total
        order.save(update_fields=["total_price", "updated_at"])