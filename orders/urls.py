from django.urls import path
from .views import *

app_name = 'orders'

urlpatterns = [
    path('checkout/process/', process_checkout, name='process_checkout'),
    path('payment/success/', payment_success, name='payment_success'),
    path('order/success/<str:order_id>/', order_success_clean, name='order_success_clean'),
]