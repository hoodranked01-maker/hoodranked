import secrets
from datetime import timedelta

import openpyxl
from openpyxl.styles import Font

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Order, OrderItem, Coupon


def naira(value):
    return f"₦{value:,.2f}" if value is not None else "—"


# ---------------------------------------------------------------- Orders
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id',
        'reference',
        'name',
        'payment_status_colored',
        'order_status_colored',
        'total_price_display',
        'coupon',
        'shipping_courier',
        'created_at',
        'item_count',
    )
    list_filter = ('payment_status', 'status', 'shipping_courier', 'coupon__kind', 'created_at')
    search_fields = ('order_id', 'reference', 'name', 'email', 'phone', 'coupon__code')
    date_hierarchy = 'created_at'
    list_select_related = ('coupon',)
    inlines = [OrderItemInline]

    # Money and Shipbubble fields are set by the checkout flow, not by hand
    readonly_fields = (
        'order_id', 'reference', 'created_at', 'updated_at',
        'subtotal_display', 'coupon', 'discount_amount', 'service_fee',
        'shipping_fee', 'total_price',
        'shipping_courier', 'shipbubble_order_id', 'shipbubble_status',
        'receiver_address_code',
    )

    fieldsets = (
        ('Order Info', {
            'fields': ('order_id', 'reference', 'user')
        }),
        ('Customer', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'postal_code')
        }),
        ('Pricing', {
            'fields': (
                'subtotal_display', 'coupon', 'discount_amount',
                'service_fee', 'shipping_fee', 'total_price',
            )
        }),
        ('Delivery', {
            'fields': (
                'shipping_courier', 'shipbubble_status', 'shipbubble_order_id',
                'receiver_address_code', 'tracking_code', 'tracking_url',
            )
        }),
        ('Status', {
            'fields': ('payment_status', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_successful_orders_excel', 'mark_as_shipped']

    # ---- list columns
    def payment_status_colored(self, obj):
        colors = {'paid': 'green', 'pending': 'orange', 'failed': 'red', 'refunded': 'purple'}
        color = colors.get(obj.payment_status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.payment_status.capitalize())
    payment_status_colored.short_description = "Payment"

    def order_status_colored(self, obj):
        colors = {
            'processing': 'blue', 'shipped': 'teal', 'delivered': 'green',
            'pending': 'orange', 'cancelled': 'red', 'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.status.capitalize())
    order_status_colored.short_description = "Order"

    def total_price_display(self, obj):
        return naira(obj.total_price)
    total_price_display.short_description = "Total"

    def subtotal_display(self, obj):
        return naira(obj.subtotal)
    subtotal_display.short_description = "Items subtotal"

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"

    # ---- actions
    @admin.action(description='Mark selected orders as shipped')
    def mark_as_shipped(self, request, queryset):
        updated_count = queryset.update(status='shipped')
        self.message_user(request, f'{updated_count} order(s) marked as shipped.')

    @admin.action(description='Export SUCCESSFUL orders to Excel')
    def export_successful_orders_excel(self, request, queryset):
        orders = (
            queryset.filter(payment_status='paid')
            .select_related('coupon')
            .prefetch_related('items__product', 'items__variant')
        )

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Successful Orders"

        headers = [
            'Order ID', 'Customer Name', 'Email', 'Phone', 'Address',
            'Payment Status', 'Order Status', 'Subtotal', 'Coupon', 'Discount',
            'Service Fee', 'Shipping Fee', 'Courier', 'Tracking URL',
            'Total Price', 'Created At', 'Order Items',
        ]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for order in orders:
            full_address = ", ".join(p for p in [order.address, order.city, order.state] if p)

            items_str = "; ".join(
                f"{item.product.name if item.product else 'Item'}"
                f"{f' ({item.variant})' if item.variant else ''}"
                f" x{item.quantity} @ ₦{item.price:,.2f}"
                for item in order.items.all()
            )

            ws.append([
                order.order_id,
                order.name,
                order.email,
                order.phone,
                full_address,
                order.payment_status,
                order.status,
                float(order.subtotal),
                order.coupon.code if order.coupon else '',
                float(order.discount_amount or 0),
                order.service_fee,
                float(order.shipping_fee or 0),
                order.shipping_courier or '',
                order.tracking_url or '',
                float(order.total_price or 0),
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                items_str,
            ])

        for col in ws.columns:
            max_len = max(len(str(c.value)) if c.value else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="successful_orders.xlsx"'
        wb.save(response)
        return response


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'product', 'variant', 'quantity', 'price', 'subtotal')
    list_filter = ('order__payment_status', 'order__status', 'product')
    search_fields = ('order__order_id', 'product__name')
    readonly_fields = ('order', 'product', 'variant', 'quantity', 'price')

    def order_link(self, obj):
        url = reverse(
            f'admin:{obj.order._meta.app_label}_{obj.order._meta.model_name}_change',
            args=[obj.order.pk],
        )
        return format_html('<a href="{}">{}</a>', url, obj.order.order_id)
    order_link.short_description = "Order"

    def subtotal(self, obj):
        return naira(obj.quantity * obj.price)
    subtotal.short_description = "Subtotal"


# --------------------------------------------------------------- Coupons
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'kind', 'value_display', 'email', 'status_colored', 'expires_at', 'created_at', 'orders_used_on')
    list_filter = ('kind', 'used', 'created_at')
    search_fields = ('code', 'email')
    date_hierarchy = 'created_at'
    actions = ['expire_now', 'extend_7_days']

    def get_readonly_fields(self, request, obj=None):
        # Codes and creation date are fixed once issued
        return ('code', 'created_at') if obj else ('created_at',)

    def get_changeform_initial_data(self, request):
        # Prefill so you can create promo codes by hand in one click
        return {
            'code': 'HR-' + secrets.token_hex(3).upper(),
            'expires_at': timezone.now() + timedelta(days=7),
        }

    def value_display(self, obj):
        return "Free delivery" if obj.kind == Coupon.FREE_DELIVERY else f"{obj.percent}% off"
    value_display.short_description = "Reward"

    def status_colored(self, obj):
        if obj.used:
            return format_html('<span style="color: gray;">Used</span>')
        if obj.expires_at <= timezone.now():
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Active</span>')
    status_colored.short_description = "Status"

    def orders_used_on(self, obj):
        return obj.orders.count()
    orders_used_on.short_description = "Orders"

    @admin.action(description='Expire selected coupons now')
    def expire_now(self, request, queryset):
        n = queryset.update(expires_at=timezone.now())
        self.message_user(request, f'{n} coupon(s) expired.')

    @admin.action(description='Extend selected coupons by 7 days')
    def extend_7_days(self, request, queryset):
        n = 0
        for coupon in queryset.filter(used=False):
            coupon.expires_at = max(coupon.expires_at, timezone.now()) + timedelta(days=7)
            coupon.save(update_fields=['expires_at'])
            n += 1
        self.message_user(request, f'{n} coupon(s) extended.')