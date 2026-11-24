from django.contrib import admin
from .models import Product, ProductImage, Variant, Collection
from django.utils.html import format_html

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
        'is_active',
        'availability_status',
        'total_stock',
        'primary_image_preview',
        'created_at'
    )
    list_filter = ('collection', 'is_available', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VariantInline]
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    actions = ['make_active', 'make_inactive']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'collection', 'category', 'description', 'price')
        }),
        ('Inventory & Status', {
            'fields': ('stock', 'is_active', 'is_available', 'is_featured')
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

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products successfully activated.')
    make_active.short_description = "Mark selected products as Active"

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products successfully deactivated.')
    make_inactive.short_description = "Mark selected products as Inactive"



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
