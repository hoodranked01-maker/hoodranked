from django.urls import path
from .views import store, product_detail

app_name = 'products'

urlpatterns = [
    path('store/', store, name='store'),
    path('product/<slug:slug>/', product_detail, name='product_detail'),
]