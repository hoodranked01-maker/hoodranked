from django.urls import path
from .views import *

app_name = 'orders'

urlpatterns = [
    path('checkout/process/', process_checkout, name='process_checkout'),
    path('payment/success/', payment_success, name='payment_success'),
    path('order/success/<str:order_id>/', order_success_clean, name='order_success_clean'),
    path('order/history/', order_history, name='order_history'),
    path('order/detail/<str:order_id>/', order_detail, name='order_detail'),
    path("track-order/", track_order, name="track_order"),
    path('orders/shipping-rates/', get_shipping_rates, name='get_shipping_rates'),
]