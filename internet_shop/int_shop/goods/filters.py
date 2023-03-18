from goods.models import Product
from django.db.models import Max, Min
from django.db.models.query import QuerySet
from decimal import Decimal


def get_max_min_price() -> tuple:
    """
    Фильтр товаров по цене
    """
    max_price = Product.objects.aggregate(max_price=Max('price'))
    min_price = Product.objects.aggregate(min_price=Min('price'))
    return max_price['max_price'], min_price['min_price']


def get_products_between_max_min_price(price_min: str, price_max: str) -> QuerySet:
    """
    Возврат товаров с ценой между
    максимальной и минимальной, указанной в фильтре
    """
    price_min = Decimal(price_min)
    price_max = Decimal(price_max)
    return Product.objects.filter(price__gte=price_min, price__lte=price_max)
