# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Collection

class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        # Add the URL names of your static pages here (homepage, about, contact)
        return ['index', 'store', 'contact', 'cart', 'shipping'] 

    def location(self, item):
        return reverse(item)

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        # Only maps out live, active inventory
        return Product.objects.filter(is_active=True) 

class CollectionSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        # Maps out all product drops/collections
        return Collection.objects.all()