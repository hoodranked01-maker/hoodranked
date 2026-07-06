# store/admin.py
from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import (
    Collection,
    Product,
    ProductImage,
    Variant,
    Order,
    OrderItem,
    Look
)


# Inline for Product Images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ('image', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; border-radius: 4px;" />', obj.image.url)
        return "No image"
    thumbnail_preview.short_description = "Preview"


# Inline for Size Variants
class VariantInline(admin.TabularInline):
    model = Variant
    extra = 3
    fields = ('size', 'additional_price', 'stock', 'stock_status')
    readonly_fields = ('stock_status',)

    def stock_status(self, obj):
        if obj.stock > 10:
            return format_html('<span style="color: green;">In stock ({})</span>', obj.stock)
        elif obj.stock > 0:
            return format_html('<span style="color: orange;">Low stock ({})</span>', obj.stock)
        else:
            return format_html('<span style="color: red;">Sold out</span>')
    stock_status.short_description = "Status"


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'collection',
        'price_display',
        'availability_status',
        'total_stock',
        'primary_image_preview',
        'created_at'
    )
    list_filter = ('collection', 'is_available', 'created_at')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VariantInline]
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'collection', 'category', 'description', 'price')
        }),
        ('Inventory & Status', {
            'fields': ('stock', 'is_available')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return f"₦{obj.price:,.2f}"
    price_display.short_description = "Price"

    def availability_status(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green;">Available</span>')
        return format_html('<span style="color: red;">Unavailable</span>')
    availability_status.short_description = "Status"

    def total_stock(self, obj):
        variant_stock = sum(v.stock for v in obj.variants.all())
        total = variant_stock + obj.stock
        if total > 10:
            return f"{total} (Good)"
        elif total > 0:
            return f"{total} (Low)"
        return "Sold out"
    total_stock.short_description = "Total Stock"

    def primary_image_preview(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary and primary.image:
            return format_html('<img src="{}" style="max-height: 60px; border-radius: 4px;" />', primary.image.url)
        elif obj.images.exists():
            first = obj.images.first()
            return format_html('<img src="{}" style="max-height: 60px; border-radius: 4px;" />', first.image.url)
        return "No image"
    primary_image_preview.short_description = "Main Image"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'thumbnail_preview', 'alt_text', 'is_primary', 'order')
    list_filter = ('product', 'is_primary')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('thumbnail_preview',)

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; border-radius: 4px;" />', obj.image.url)
        return "No image"
    thumbnail_preview.short_description = "Preview"


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'additional_price_display', 'stock', 'stock_status')
    list_filter = ('product', 'size')
    search_fields = ('product__name', 'size')
    readonly_fields = ('stock_status',)

    def additional_price_display(self, obj):
        if obj.additional_price > 0:
            return f"+₦{obj.additional_price:,.2f}"
        return "—"
    additional_price_display.short_description = "Extra Price"

    def stock_status(self, obj):
        if obj.stock > 10:
            return format_html('<span style="color: green;">In stock</span>')
        elif obj.stock > 0:
            return format_html('<span style="color: orange;">Low stock</span>')
        else:
            return format_html('<span style="color: red;">Sold out</span>')
    stock_status.short_description = "Status"


# Order Admin – Updated with new fields
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

@admin.register(Look)
class LookAdmin(admin.ModelAdmin):
    list_display = (
        "look_number",
        "thumbnail",
        "title",
        "season",
        "model_name",
        "is_published",
    )
    list_display_links = ("thumbnail", "title")
    list_editable = ("look_number", "is_published")
    list_filter = ("is_published", "season")
    search_fields = ("title", "model_name", "photographer_credit")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("look_number",)
 
    fieldsets = (
        (None, {"fields": ("look_number", "title", "slug", "image", "caption")}),
        ("Credits", {"fields": ("season", "model_name", "photographer_credit")}),
        ("Visibility", {"fields": ("is_published",)}),
    )
 
    @admin.display(description="Preview")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;width:38px;object-fit:cover;border:1px solid #333;">',
                obj.image.url,
            )
        return "—"