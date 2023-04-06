from goods.models import Product
from django.db.models import Max, Min
from django.db.models.query import QuerySet
from decimal import Decimal
from django.core.cache import cache


def get_max_min_price(category_slug: str) -> tuple:
    """
    Возврат максимальной и минимальной цены товаров
    для категории с category_slug
    """

    # достаем из кеша, если цены там есть
    max_price = cache.get(f'max_price_{category_slug}')
    min_price = cache.get(f'min_price_{category_slug}')

    # кешируем цены по категориям, если их нет в кеше
    if max_price and min_price:
        return max_price['max_price'], min_price['min_price']
    else:
        max_price = Product.objects.filter(category__slug=category_slug).aggregate(max_price=Max('price'))
        min_price = Product.objects.filter(category__slug=category_slug).aggregate(min_price=Min('price'))
        cache.set_many({f'max_price_{category_slug}': max_price, f'min_price_{category_slug}': min_price}, None)
        return max_price['max_price'], min_price['min_price']


def get_products_between_max_min_price(price_min: str, price_max: str) -> QuerySet:
    """
    Возврат товаров с ценой между
    максимальной и минимальной, указанной в фильтре
    """
    price_min = Decimal(price_min)
    price_max = Decimal(price_max)
    return Product.objects.filter(price__gte=price_min, price__lte=price_max)
