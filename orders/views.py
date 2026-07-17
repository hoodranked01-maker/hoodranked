import os
from django.shortcuts import render, get_object_or_404, redirect, reverse
from .models import Order, OrderItem
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import requests
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

paystack = os.getenv('PAYSTACK_SECRET_KEY')

@require_POST
@csrf_exempt
def process_checkout(request):
    try:
        data = json.loads(request.body)
        cart_items = data.get('cart_items', [])

        if not cart_items:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        service_fee = int(data.get('service_fee', 0))
        items_total = sum(item['price'] * item['quantity'] for item in cart_items)
        total = items_total + service_fee

        user = request.user if request.user.is_authenticated else None

        order = Order.objects.create(
            user=user,
            name=data.get('full_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postal_code', ''),
            total_price=total,
            service_fee=service_fee,
            payment_status='pending',
            status='pending'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_id=item.get('product_id'),
                variant_id=item.get('variant_id'),
                quantity=item['quantity'],
                price=item['price']
            )

        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json",
        }

        payload = {
            "email": order.email,
            "amount": int(total * 100),
            # "split_code": "SPL_nhsUhQOZ0k", 
            "reference": order.reference,
            "callback_url": request.build_absolute_uri(f"/payment/success/"),
            "metadata": {
                "order_id": str(order.order_id),
                "custom_fields": [
                    {"display_name": "Name", "variable_name": "name", "value": order.name},
                    {"display_name": "Phone", "variable_name": "phone", "value": order.phone}
                ]
            }
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()

        resp_data = response.json()

        if resp_data.get('status'):
            return JsonResponse({
                'success': True,
                'authorization_url': resp_data['data']['authorization_url']
            })
        else:
            order.payment_status = 'failed'
            order.status = 'failed'
            order.save()
            return JsonResponse({'error': resp_data.get('message', 'Failed')}, status=400)

    except Exception as e:
        if 'order' in locals():
            order.payment_status = 'failed'
            order.status = 'failed'
            order.save()
        return JsonResponse({'error': str(e)}, status=500)
    
def payment_success(request):
    reference = request.GET.get('reference') or request.GET.get('trxref')
    
    if not reference:
        logger.warning("No reference received in Paystack callback")
        return redirect('cart')

    order = get_object_or_404(Order, reference=reference)

    if order.payment_status == 'paid':
        return redirect('order_success_clean', order_id=order.order_id)

    headers = {"Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"}
    
    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{reference}",
            headers=headers,
            timeout=12
        )
        response.raise_for_status()
        data = response.json()

        if data.get('status') and data['data']['status'] == 'success':
            order.payment_status = 'paid'
            order.status = 'processing'
            order.save()

            request.session['clear_cart_after_success'] = True
            
            logger.info(f"Payment VERIFIED & SUCCESS for order {order.order_id} - ref: {reference}")
            return redirect('orders:order_success_clean', order_id=order.order_id)
        
        else:
            order.payment_status = 'failed'
            order.status = 'failed'
            order.save()
            logger.warning(f"Payment failed verification for ref {reference}: {data.get('message')}")
            return redirect('order_failed')

    except Exception as e:
        logger.error(f"Paystack verify request failed for ref {reference}: {str(e)}")
        order.payment_status = 'failed'
        order.status = 'failed'
        order.save()
        return redirect('order_failed')
    
def order_success_clean(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
        
    return render(request, 'store/order_success.html', {
        'order': order,
        'should_clear_cart': request.session.get('clear_cart_after_success', False)
    })

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_orders(request):
    queryset = Order.objects.filter(payment_status='paid').order_by('-created_at')

    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(order_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(reference__icontains=search_query)
        )

    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    queryset = queryset.prefetch_related('items')

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    context = {
        'orders': orders,
        'search_query': search_query,
    }
    return render(request, 'admin/orders.html', context)

@user_passes_test(lambda u: u.is_superuser)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            order.status = new_status
            order.save()
            messages.success(request, f'Order {order.order_id} marked as {new_status}.')
    
    return redirect('admin_orders')

ORDER_STATUS_STEPS = [
    ("Pending", "pending"),
    ("Processing", "processing"),
    ("Shipped", "shipped"),
    ("Delivered", "delivered"),
]
_STATUS_KEYS = [key for _, key in ORDER_STATUS_STEPS]
 
 
@login_required
def order_history(request):
    orders_qs = Order.objects.filter(user=request.user)
 
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
 
    context = {
        "orders": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
    }
    return render(request, "orders/order_history.html", context)
 
 
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
 
    # Line items: this assumes an OrderItem-style model related to Order via
    # `order.items`. Swap `order.items.all()` for whatever your actual related
    # name is — if there's no such model yet, this just renders the
    # "item details aren't available" fallback in the template.
    order_items = order.items.all() if hasattr(order, "items") else None
 
    order_status_index = (
        _STATUS_KEYS.index(order.status) if order.status in _STATUS_KEYS else -1
    )
 
    context = {
        "order": order,
        "order_items": order_items,
        "order_status_steps": ORDER_STATUS_STEPS,
        "order_status_index": order_status_index,
    }
    return render(request, "orders/order_detail.html", context)

def track_order(request):
    """
    Guest-accessible order lookup — no login required. Looks up by order_id
    + email together so a leaked/guessed order_id alone can't expose someone
    else's shipping address.
    """
    order = None
    error = None
    submitted_order_id = request.GET.get("order_id", "").strip()
    submitted_email = request.GET.get("email", "").strip()
 
    if submitted_order_id and submitted_email:
        try:
            order = Order.objects.get(
                order_id__iexact=submitted_order_id,
                email__iexact=submitted_email,
            )
        except Order.DoesNotExist:
            error = "We couldn't find an order matching that ID and email. Double-check both and try again."
 
    context = {
        "order": order,
        "error": error,
        "submitted_order_id": submitted_order_id,
        "submitted_email": submitted_email,
    }
 
    if order:
        order_status_index = (
            _STATUS_KEYS.index(order.status) if order.status in _STATUS_KEYS else -1
        )
        context["order_status_steps"] = ORDER_STATUS_STEPS
        context["order_status_index"] = order_status_index
 
    return render(request, "orders/track_order.html", context)