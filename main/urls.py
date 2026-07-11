from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from orders.views import admin_orders, update_order_status

urlpatterns = [
    path('admin/orders/', admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/update-status/', update_order_status, name='update_order_status'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('store.urls')),
    path('', include('products.urls')),
    path('', include('orders.urls')),
]
handler400 = 'store.views.bad_request'
handler403 = 'store.views.permission_denied'
handler404 = 'store.views.page_not_found'
handler500 = 'store.views.internal_server_error'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)