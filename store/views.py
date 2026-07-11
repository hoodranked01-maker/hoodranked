import os
from django.shortcuts import render, get_object_or_404, redirect
from .models import Look
from products.models import Product

def index(request):
    products = Product.objects.all()[:4]
    context = {
        'products': products,
    }
    return render(request, 'store/index.html', context)

def contact(request):
    return render(request, 'store/contact.html')

def cart(request):
    return render(request, 'store/cart.html')

def checkout(request):
    return render(request, 'store/checkout.html')
    
def thank_you(request):
    return render(request, 'store/thanks.html')
    
def privacy(request):
    return render(request, 'store/privacy.html')
    
def terms(request):
    return render(request, 'store/terms.html')
    
def shipping(request):
    return render(request, 'store/shipping.html')

def lookbook(request):
    looks = Look.objects.filter(is_published=True)
    return render(request, "store/lookbook.html", {"looks": looks})
 
def lookbook_detail(request, slug):
    look = get_object_or_404(Look, slug=slug, is_published=True)
    next_look = (
        Look.objects.filter(is_published=True, look_number__gt=look.look_number)
        .order_by("look_number")
        .first()
    )
    prev_look = (
        Look.objects.filter(is_published=True, look_number__lt=look.look_number)
        .order_by("-look_number")
        .first()
    )
    context = {"look": look, "next_look": next_look, "prev_look": prev_look}
    return render(request, "store/lookbook_detail.html", context)
    
def bad_request(request, exception):
    return render(request, 'errors/400.html', status=400)

def permission_denied(request, exception):
    return render(request, 'errors/403.html', status=403)
    
def page_not_found(request, exception):
    return render(request, 'errors/404.html', status=404)
    
def internal_server_error(request):
    return render(request, 'errors/500.html', status=500)