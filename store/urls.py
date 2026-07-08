from django.urls import path
from .views import index, cart, checkout, thank_you, contact, lookbook, lookbook_detail

app_name = 'store'

urlpatterns = [
    path('', index, name='index'),
    path('contact/', contact, name='contact'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('thank-you/', thank_you, name='thank_you'),
    path("lookbook/", lookbook, name="lookbook"),
    path("lookbook/<slug:slug>/", lookbook_detail, name="lookbook_detail"),
]