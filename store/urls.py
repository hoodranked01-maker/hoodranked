from django.urls import path
from .views import index, cart, checkout, shipping, terms, thank_you, contact, lookbook, lookbook_detail, privacy, test
from store.wheel import spin_wheel

app_name = 'store'

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('', index, name='index'),
    path('contact/', contact, name='contact'),
    path('cart/', cart, name='cart'),
    path('checkout/', checkout, name='checkout'),
    path('thank-you/', thank_you, name='thank_you'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),
    path('shipping/', shipping, name='shipping'),
    path("lookbook/", lookbook, name="lookbook"),
    path("lookbook/<slug:slug>/", lookbook_detail, name="lookbook_detail"),
    path("test/", test, name="test"),
    path('sentry-debug/', trigger_error),
    path('spin/', spin_wheel, name='spin_wheel'),
]