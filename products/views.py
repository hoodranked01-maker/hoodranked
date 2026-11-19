from django.shortcuts import render, get_object_or_404
from .models import Product, Collection
from decimal import Decimal
from django.db.models import Q
from django.views.decorators.cache import cache_page

def store(request):
    products_list = Product.objects.filter(is_active=True)

    collection_id = request.GET.get('collection', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    search_query = request.GET.get('q', '') 
    sort = request.GET.get('sort', 'newest')

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

    collections = Collection.objects.all()

    context = {
        'products': products_list,
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