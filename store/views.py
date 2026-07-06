import os
from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import requests
from .models import Order, OrderItem, Product, Variant, Collection, Look
from django.contrib.auth.decorators import user_passes_test
import json
from decimal import Decimal
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Order, OrderItem, Product, Variant
import logging
from django.contrib import messages

logger = logging.getLogger(__name__)

# Create your views here.

def index(request):
    products = Product.objects.all()[:4]
    context = {
        'products': products,
    }
    return render(request, 'store/index.html', context)

def store(request):
    products_list = Product.objects.all()

    collection_id = request.GET.get('collection')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('q') 

    if collection_id:
        try:
            collection = Collection.objects.get(id=collection_id)
            products_list = products_list.filter(collection=collection)
        except Collection.DoesNotExist:
            pass

    if min_price:
        try:
            products_list = products_list.filter(price__gte=Decimal(min_price))
        except:
            pass

    if max_price:
        try:
            products_list = products_list.filter(price__lte=Decimal(max_price))
        except:
            pass

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_asc':
        products_list = products_list.order_by('price')
    elif sort == 'price_desc':
        products_list = products_list.order_by('-price')
    elif sort == 'name_asc':
        products_list = products_list.order_by('name')
    elif sort == 'name_desc':
        products_list = products_list.order_by('-name')
    else:
        products_list = products_list.order_by('-created_at')

    # paginator = Paginator(products_list, 8)
    # page = request.GET.get('page')

    # try:
    #     products = paginator.page(page)
    # except PageNotAnInteger:
    #     products = paginator.page(1)
    # except EmptyPage:
    #     products = paginator.page(paginator.num_pages)
    
    products = products_list

    collections = Collection.objects.all()

    context = {
        'products': products,
        # 'paginator': paginator,
        'collections': collections,
        'current_filters': {
            'collection': collection_id,
            'min_price': min_price,
            'max_price': max_price,
            'q': search_query,
            'sort': sort,
        }
    }

    return render(request, 'store/store.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    context = {
        'product': product,
    }
    return render(request, 'store/product_detail.html', context)

def contact(request):
    return render(request, 'store/contact.html')

def cart(request):
    return render(request, 'store/cart.html')

def checkout(request):
    return render(request, 'store/checkout.html')

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

        order = Order.objects.create(
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
                product_id=item.get('product_id'),     # if you send it
                variant_id=item.get('variant_id'),
                quantity=item['quantity'],
                price=item['price']
            )

        # Paystack initialization
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json",
        }

        payload = {
            "email": order.email,
            "amount": int(total * 100),  # kobo
            "split_code": "SPL_nhsUhQOZ0k", 
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
        return redirect('cart')  # or a failed page

    order = get_object_or_404(Order, reference=reference)

    # Skip if already paid (idempotency)
    if order.payment_status == 'paid':
        return redirect('order_success_clean', order_id=order.order_id)

    # Verify transaction
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
            order.status = 'processing'  # or 'confirmed'
            order.save()

            # Mark session to clear cart on success page
            request.session['clear_cart_after_success'] = True
            
            logger.info(f"Payment VERIFIED & SUCCESS for order {order.order_id} - ref: {reference}")
            return redirect('order_success_clean', order_id=order.order_id)
        
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
    
def thank_you(request):
    return render(request, 'store/thanks.html')

@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_orders(request):
    queryset = Order.objects.filter(payment_status='paid').order_by('-created_at')

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(order_id__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(reference__icontains=search_query)
        )

    # Status Filter
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)

    # Prefetch related items
    queryset = queryset.prefetch_related('items')

    # Pagination
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    context = {
        'orders': orders,
        'search_query': search_query,   # To keep search term in input
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

def lookbook(request):
    looks = Look.objects.filter(is_published=True)
    return render(request, "store/lookbook.html", {"looks": looks})
 
 
def lookbook_detail(request, slug):
    look = get_object_or_404(Look, slug=slug, is_published=True)
    next_look = (
        Look.objects.filter(is_published=True, look_number__gt=look.look_number)
        .order_by("look_number")
        .first()
    )
    prev_look = (
        Look.objects.filter(is_published=True, look_number__lt=look.look_number)
        .order_by("-look_number")
        .first()
    )
    context = {"look": look, "next_look": next_look, "prev_look": prev_look}
    return render(request, "store/lookbook_detail.html", context)