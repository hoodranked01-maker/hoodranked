from django.urls import path
from .views import index, store, product_detail, cart, checkout, process_checkout, payment_success, order_success_clean, thank_you, contact, admin_orders, update_order_status, lookbook, lookbook_detail

urlpatterns = [
    path('', index, name='index'),
    path('store/', store, name='store'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
    path('contact/', contact, name='contact'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('checkout/process/', process_checkout, name='process_checkout'),
    path('payment/success/', payment_success, name='payment_success'),
    path('order/success/<str:order_id>/', order_success_clean, name='order_success_clean'),
    path('thank-you/', thank_you, name='thank_you'),
    path("lookbook/", lookbook, name="lookbook"),
    path("lookbook/<slug:slug>/", lookbook_detail, name="lookbook_detail"),
]