import os
import shutil

import boto3
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from common.moduls_init import redis
from common.storage_backends import MediaStorage
from goods.models import Product, Property, PropertyCategory


@receiver(signal=[post_save, post_delete], sender=Product)
def invalidate_prices_cache(sender, instance: Product, *args, **kwargs):
    """
    Invalidate the cache of maximum or minimum price for product category,
    when adding the new product or deleting the existing product
    """
    max_price = cache.get(f'max_price_{instance.category.slug}')
    min_price = cache.get(f'min_price_{instance.category.slug}')

    if max_price and (instance.price > max_price['max_price'] or instance.price == max_price['max_price']):
        cache.delete(f'max_price_{instance.category.slug}')
    if min_price and (instance.price < min_price['min_price'] or instance.price == min_price['min_price']):
        cache.delete(f'min_price_{instance.category.slug}')


def invalidate_properties_cache(sender, instance, **kwargs):
    """
    Invalidate the cache for storage queryset with products properties,
    when adding the new property or property category
    """

    if isinstance(instance, Property):
        category = instance.product.category.slug
        cache.delete(f'category_{category}_props')
    elif isinstance(instance, PropertyCategory):
        categories = instance.product_categories.all()
        for c in categories:
            cache.delete(f'category_{c.slug}_props')


@receiver(signal=post_delete, sender=Product)
def delete_product_images_folder(sender, product: Product, *args, **kwargs):
    """
    Deleting product image from AWS Bucket,
    deleting directory with product photos from media root,
    and deleting product id from Redis
    """
    # if using AWS Cloud storage
    if isinstance(product.image.storage, MediaStorage):
        aws_image_key = f'media/{product.image.name}'
        aws_s3_bucket = MediaStorage().bucket_name
        client = boto3.client('s3')
        client.delete_object(Bucket=aws_s3_bucket, Key=aws_image_key)
    # deleting product's photo directory from the file system
    shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{product.name}'))
    redis.srem('products_ids', product.pk)
