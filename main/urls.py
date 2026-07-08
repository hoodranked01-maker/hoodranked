from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from orders.views import admin_orders, update_order_status

urlpatterns = [
    path('admin/orders/', admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/update-status/', update_order_status, name='update_order_status'),
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('', include('products.urls')),
    path('', include('orders.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)