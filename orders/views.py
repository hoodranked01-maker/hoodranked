import os
from django.shortcuts import render, get_object_or_404, redirect, reverse

from main import settings
from .models import Order, OrderItem, Coupon
from products.models import Variant
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
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from decimal import Decimal
from .services.shipbubble import validate_address, fetch_rates, create_shipment
from .coupons import get_valid_coupon, apply_coupon

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

        # ---------- SERVER-SIDE VALIDATION ----------
        validated_items = []
        calculated_subtotal = Decimal('0.00')

        for item in cart_items:
            variant_id = item.get('variant_id')
            quantity = int(item.get('quantity', 1))
            client_price = Decimal(str(item.get('price', 0)))

            if not variant_id or quantity < 1:
                return JsonResponse({
                    'error': 'Invalid cart item',
                    'code': 'INVALID_CART'
                }, status=400)

            try:
                variant = Variant.objects.select_related('product').get(id=variant_id)
            except Variant.DoesNotExist:
                return JsonResponse({
                    'error': 'Product no longer available',
                    'code': 'ITEM_NOT_FOUND'
                }, status=400)

            # Real price from database
            real_price = variant.product.price + variant.additional_price

            # Price mismatch → cheeky boy
            if client_price != real_price:
                return JsonResponse({
                    'error': 'Price mismatch detected',
                    'code': 'PRICE_MISMATCH'
                }, status=400)

            # Stock check
            # if variant.available_stock < quantity:
            #     return JsonResponse({
            #         'error': f'Only {variant.available_stock} left for {variant.product.name} ({variant.size})',
            #         'code': 'INSUFFICIENT_STOCK'
            #     }, status=400)

            validated_items.append({
                'variant': variant,
                'quantity': quantity,
                'price': real_price,
            })
            calculated_subtotal += real_price * quantity

        service_fee = int(data.get('service_fee', 0))
        shipping_fee = Decimal(str(data.get('shipping_fee', 0)))

        # ---------- COUPON (validated again on the server) ----------
        coupon = None
        discount = Decimal('0.00')
        code = (data.get('coupon_code') or '').strip()
        if code:
            coupon, err = get_valid_coupon(code, data.get('email'))
            if err:
                return JsonResponse({'error': err, 'code': 'INVALID_COUPON'}, status=400)
            discount, shipping_fee = apply_coupon(coupon, calculated_subtotal, shipping_fee)

        total = calculated_subtotal - discount + Decimal(service_fee) + shipping_fee

        # ---------- CREATE ORDER ----------
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
            service_fee=service_fee,
            shipping_fee=shipping_fee,
            shipping_courier=data.get("shipping_courier", ""),
            shipbubble_request_token=data.get("request_token", ""),
            shipbubble_service_code=data.get("service_code", ""),
            shipbubble_courier_id=data.get("courier_id", ""),
            receiver_address_code=data.get("receiver_address_code"),
            coupon=coupon,
            discount_amount=discount,
            total_price=total,
            payment_status='pending',
            status='pending'
        )

        for item in validated_items:
            OrderItem.objects.create(
                order=order,
                product=item['variant'].product,
                variant=item['variant'],
                quantity=item['quantity'],
                price=item['price']
            )

        # ---------- PAYSTACK ----------
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json",
        }

        payload = {
            "email": order.email,
            "amount": int(order.total_price * 100),
            "reference": order.reference,
            # "split_code": "SPL_nhsUhQOZ0k",
            "callback_url": request.build_absolute_uri("/payment/success/"),
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
            return JsonResponse({'error': resp_data.get('message', 'Payment initialization failed')}, status=400)

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
        return redirect('store:cart')

    order = get_object_or_404(Order, reference=reference)

    if order.payment_status == 'paid':
        return redirect('orders:order_success_clean', order_id=order.order_id)

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

            if order.coupon_id:
                Coupon.objects.filter(pk=order.coupon_id, used=False).update(used=True)
                request.session.get('wheel', {}).pop('code', None)
                request.session.modified = True

            # Create Shipbubble shipment
            if order.shipbubble_request_token and order.shipbubble_service_code:
                try:
                    shipment = create_shipment(
                        order.shipbubble_request_token,
                        order.shipbubble_service_code,
                        order.shipbubble_courier_id
                    )
                    order.shipbubble_order_id = shipment.get("order_id")
                    order.tracking_url = shipment.get("tracking_url", "")
                    order.shipbubble_status = shipment.get("status", "pending")
                    order.shipping_courier = shipment.get("courier", {}).get("name", order.shipping_courier)
                    order.save()
                    logger.info(f"Shipbubble shipment created for {order.order_id}: {order.shipbubble_order_id}")
                except Exception as e:
                    logger.error(f"Shipbubble create failed for {order.order_id}: {e}")

            try:
                subject = f"Order Confirmed – #{order.order_id}"
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [order.email]

                context = {
                    "order": order,
                    "user": order.user if order.user_id else None,
                }

                text_content = render_to_string("account/email/order_confirmation.txt", context)
                html_content = render_to_string("account/email/order_confirmation.html", context)

                msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                logger.info(f"Order confirmation email sent for {order.order_id}")
            except Exception as e:
                logger.error(f"Failed to send order confirmation for {order.order_id}: {e}")
                
            request.session['clear_cart_after_success'] = True
            
            logger.info(f"Payment VERIFIED & SUCCESS for order {order.order_id} - ref: {reference}")
            return redirect('orders:order_success_clean', order_id=order.order_id)
        
        else:
            order.payment_status = 'failed'
            order.status = 'failed'
            order.save()
            logger.warning(f"Payment failed verification for ref {reference}: {data.get('message')}")
            return redirect('orders:order_failed')

    except Exception as e:
        logger.error(f"Paystack verify request failed for ref {reference}: {str(e)}")
        order.payment_status = 'failed'
        order.status = 'failed'
        order.save()
        return redirect('orders:order_failed')
    
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

@require_POST
@csrf_exempt
def get_shipping_rates(request):
    try:
        data = json.loads(request.body)
        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")
        address = data.get("address")
        city = data.get("city")
        state = data.get("state")
        cart_items = data.get("cart_items", [])

        if not all([full_name, email, phone, address, city, state, cart_items]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        full_address = f"{address}, {city}, {state}, Nigeria"
        validated = validate_address(full_name, email, phone, full_address)
        receiver_code = validated["address_code"]

        package_items = []
        for item in cart_items:
            variant = Variant.objects.select_related("product").get(id=item["variant_id"])
            package_items.append({
                "name": variant.product.name,
                "description": f"{variant.product.name} ({variant.size})",
                "unit_weight": float(variant.product.weight or 0.5),
                "unit_amount": float(variant.product.price + variant.additional_price),
                "quantity": int(item["quantity"]),
            })

        rates_data = fetch_rates(receiver_code, package_items)

        return JsonResponse({
            "success": True,
            "request_token": rates_data["request_token"],
            "couriers": rates_data["couriers"],
            "receiver_address_code": receiver_code,
            "formatted_address": validated.get("formatted_address"),
            "validated_city": validated.get("city"),
            "validated_state": validated.get("state"),
        })
    except Exception as e:
        logger.error(f"Shipbubble rate error: {e}")
        return JsonResponse({"error": str(e)}, status=400)

@require_POST
def apply_coupon_view(request):
    try:
        data = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"valid": False, "error": "Bad request"}, status=400)

    coupon, err = get_valid_coupon(data.get("code"), data.get("email"))
    if err:
        return JsonResponse({"valid": False, "error": err}, status=400)

    return JsonResponse({
        "valid": True,
        "code": coupon.code,
        "kind": coupon.kind,
        "percent": coupon.percent,
    })