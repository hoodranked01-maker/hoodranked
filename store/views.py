import os
from django.shortcuts import render
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