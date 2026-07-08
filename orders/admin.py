from django.contrib import admin
from .models import Order, OrderItem
from django.utils.html import format_html

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id',
        'reference',
        'name',
        'payment_status_colored',
        'order_status_colored',
        'total_price_display',
        'created_at',
        'item_count'
    )
    list_filter = ('payment_status', 'status', 'created_at')
    search_fields = ('order_id', 'reference', 'name', 'email', 'phone')
    date_hierarchy = 'created_at'
    readonly_fields = ('order_id', 'reference', 'created_at', 'updated_at', 'total_price')
    inlines = []  # We'll add OrderItem inline below

    fieldsets = (
        ('Order Info', {
            'fields': ('order_id', 'reference', 'total_price')
        }),
        ('Customer', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Shipping', {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        ('Status', {
            'fields': ('payment_status', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def payment_status_colored(self, obj):
        colors = {
            'paid': 'green',
            'pending': 'orange',
            'failed': 'red',
            'refunded': 'purple',
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.payment_status.capitalize())
    payment_status_colored.short_description = "Payment"

    def order_status_colored(self, obj):
        colors = {
            'processing': 'blue',
            'shipped': 'teal',
            'delivered': 'green',
            'pending': 'orange',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.status.capitalize())
    order_status_colored.short_description = "Order"

    def total_price_display(self, obj):
        return f"₦{obj.total_price:,.2f}"
    total_price_display.short_description = "Total"

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"


# Inline for Order Items
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'price')


OrderAdmin.inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'product', 'variant', 'quantity', 'price', 'subtotal')
    list_filter = ('order__payment_status', 'order__status', 'product')
    search_fields = ('order__order_id', 'product__name')
    readonly_fields = ('order', 'product', 'variant', 'quantity', 'price')

    def order_link(self, obj):
        return format_html('<a href="/admin/store/order/{}/change/">{}</a>', obj.order.id, obj.order.order_id)
    order_link.short_description = "Order"

    def subtotal(self, obj):
        return f"₦{(obj.quantity * obj.price):,.2f}"
    subtotal.short_description = "Subtotal"
