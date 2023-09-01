from django.core.cache import cache
from django.db.models import Max, Min

from goods.models import Product


def get_max_min_price(category_slug: str) -> tuple:
    """
    Returns maximum and minimum products price for category with category_slug
    """

    # get prices from cache if they are existing
    max_price = cache.get(f'max_price_{category_slug}')
    min_price = cache.get(f'min_price_{category_slug}')

    # caching prices by categories, if they are no in the cache yet
    if max_price and min_price:
        return max_price['max_price'], min_price['min_price']
    else:
        max_price = Product.objects.filter(category__slug=category_slug).aggregate(max_price=Max('price'))
        min_price = Product.objects.filter(category__slug=category_slug).aggregate(min_price=Min('price'))
        cache.set_many({f'max_price_{category_slug}': max_price, f'min_price_{category_slug}': min_price}, None)
        return max_price['max_price'], min_price['min_price']
