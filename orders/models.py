import secrets
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from psycopg import logger
from products.models import Product, Variant
import random
import string

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='orders'
    )
    
    order_id = models.CharField(max_length=50, unique=True, editable=True, null=True, blank=True)
    reference = models.CharField(max_length=100, unique=True, editable=True, null=True, blank=True)

    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=14, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

    # ---------- Shipbubble / Shipping fields ----------
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    shipping_courier = models.CharField(max_length=100, blank=True, null=True)
    shipbubble_request_token = models.CharField(max_length=255, blank=True, null=True)
    shipbubble_service_code = models.CharField(max_length=100, blank=True, null=True)
    shipbubble_courier_id = models.CharField(max_length=100, blank=True, null=True)
    shipbubble_order_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_code = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    shipbubble_status = models.CharField(max_length=50, blank=True, null=True)
    receiver_address_code = models.IntegerField(null=True, blank=True)

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
    def subtotal(self):
        return self.price * self.quantity

class Coupon(models.Model):
    FREE_DELIVERY = "free_delivery"
    PERCENT = "percent"
    KIND_CHOICES = [(FREE_DELIVERY, "Free delivery"), (PERCENT, "Percent off")]

    code = models.CharField(max_length=20, unique=True, db_index=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    percent = models.PositiveSmallIntegerField(default=0)   # used when kind == PERCENT
    email = models.EmailField(blank=True)                   # who won it
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    @classmethod
    def issue(cls, kind, percent=0, email="", days=7):
        return cls.objects.create(
            code="HR-" + secrets.token_hex(3).upper(),
            kind=kind, percent=percent, email=email,
            expires_at=timezone.now() + timedelta(days=days),
        )

    def __str__(self):
        return self.code