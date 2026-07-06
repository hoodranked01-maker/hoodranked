from django.db import models
from django.urls import reverse
import uuid
import random
import string

class Collection(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='collections/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, related_name='products')
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    CATEGORY_CHOICES = [
        ('hoodies', 'Hoodies'),
        ('tees', 'T-Shirts'),
        ('accessories', 'Accessories'),
        ('limited', 'Limited Drops'),
        ('other', 'Other'),
    ]

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        db_index=True
    )

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
    def get_primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        return primary.image.url if primary else self.image.url if self.image else None
    
    def get_gallery_images(self):
        return self.images.all()
    
    @property
    def is_sold_out(self):
        return not self.variants.filter(stock__gt=0).exists()
    
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product.name} ({self.order})"

class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('product', 'size')
        verbose_name = "Size Variant"
        verbose_name_plural = "Size Variants"

    def __str__(self):
        return f"{self.product.name} - {self.size}"

class Order(models.Model):
    order_id = models.CharField(max_length=50, unique=True, editable=True, null=True, blank=True)
    reference = models.CharField(max_length=100, unique=True, editable=True, null=True, blank=True)

    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=14, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    service_fee = models.IntegerField(default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']

    def generate_order_id(self):
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return f"HR-{random_part}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            while True:
                candidate = self.generate_order_id()
                if not Order.objects.filter(order_id=candidate).exists():
                    self.order_id = candidate
                    self.reference = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_id

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def get_subtotal(self):
        return self.price * self.quantity

class Look(models.Model):
    """A single spread in the lookbook. Ordered by look_number, which is a real
    sequence (the order the collection was shot/dropped in) — not decoration."""
 
    title = models.CharField(max_length=120, help_text="e.g. 'Midnight Run'")
    slug = models.SlugField(unique=True)
    look_number = models.PositiveIntegerField(unique=True, help_text="Position in the lookbook, e.g. 1 for LOOK 01")
    season = models.CharField(max_length=60, blank=True, help_text="e.g. 'FW25' — shown as a small tag")
    image = models.ImageField(upload_to="lookbook/")
    caption = models.CharField(max_length=200, blank=True, help_text="Short editorial line under the title")
    model_name = models.CharField(max_length=120, blank=True)
    photographer_credit = models.CharField(max_length=120, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["look_number"]
        verbose_name = "Look"
        verbose_name_plural = "Lookbook"
 
    def __str__(self):
        return f"Look {self.look_number:02d} — {self.title}"
 
    def get_absolute_url(self):
        return reverse("lookbook_detail", args=[self.slug])

