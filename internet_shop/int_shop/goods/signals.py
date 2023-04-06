from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from goods.models import Product


@receiver(signal=[post_save, post_delete], sender=Product)
def invalidate_prices_cache(sender, instance: Product, *args, **kwargs):
    """
    Инвалидаирование кеша максимальной или минимальной
    цены из всех цен товаров для категории, которой принадлежит instance
    при добавлении нового товара или при удалении
    """
    max_price = cache.get(f'max_price_{instance.category.slug}')
    min_price = cache.get(f'min_price_{instance.category.slug}')

    if max_price and (instance.price > max_price['max_price'] or instance.price == max_price['max_price']):
        cache.delete(f'max_price_{instance.category.slug}')
    if min_price and (instance.price < min_price['min_price'] or instance.price == min_price['min_price']):
        cache.delete(f'min_price_{instance.category.slug}')

    return
