from django.db import models
from django.urls import reverse

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
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    weight = models.DecimalField(
        max_digits=6, 
        decimal_places=3, 
        default=0.5,
        help_text="Weight in KG"
    )
    
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

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
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
        product_name = self.product.name if self.product_id else "No product"
        return f"{product_name} - {self.size}"