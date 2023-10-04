import os
import shutil
from decimal import Decimal
from random import randint
from unittest.mock import patch

import redis
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.test import TestCase

from goods.models import Product, Category, Manufacturer, PropertyCategory, Property


class TestGoodsSignals(TestCase):

    def setUp(self) -> None:
        self.random_number = randint(1, 50)
        self.category_1 = Category.objects.create(name=f'Category_{self.random_number}',
                                                  slug=f'category-{self.random_number}')

        self.manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                         slug=f'manufacturer_{self.random_number}',
                                                         description='Description')

        self.product1 = Product.objects.create(id=1000005,
                                               name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=self.manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=self.category_1)

        self.property_category = PropertyCategory.objects.create(name=f'property_category_{self.random_number}')
        self.property1 = Property.objects.create(name='Color',
                                                 text_value='Green',
                                                 category_property=self.property_category,
                                                 product=self.product1)

        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('common.moduls_init.redis', redis_instance)
        self.redis = redis_patcher.start()

    def test_invalidate_prices_cache(self):
        """
        Checking signal, that invalidates cache of maximum and minimum price
        for product category, when adding the new product or deleting the existing product
        """
        # set data in cache
        cache.set_many({f'max_price_{self.category_1.slug}': {'max_price': self.product1.price},
                        f'min_price_{self.category_1.slug}': {'min_price': self.product1.price}})
        # check whether data are in cache
        self.assertEqual(cache.get(f'max_price_{self.category_1.slug}'), {'max_price': self.product1.price})
        self.assertEqual(cache.get(f'min_price_{self.category_1.slug}'), {'min_price': self.product1.price})

        self.product2 = Product(name=f'Product_{self.random_number + 1}',
                                slug=f'product_{self.random_number + 1}',
                                manufacturer=self.manufacturer1,
                                price=Decimal('300.25'),
                                description='Description',
                                category=self.category_1)

        # simulate connecting the signal with transmitter of this signal
        with patch('goods.signals.invalidate_prices_cache', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Product)
            self.product2.save()  # action that leading to the signal sendr

        # number of callings of the signal must be not greater than 1
        self.assertEqual(mocked_handler.call_count, 1)
        cache_after_test = cache.get_many(f'max_price_{self.product2.category.slug}',
                                          f'min_price_{self.product2.category.slug}')
        self.assertFalse(cache_after_test)  # must be nothing
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))
        self.redis.srem('products_ids', self.product2.pk)

        # set data in cache
        cache.set_many({f'max_price_{self.category_1.slug}': {'max_price': self.product1.price},
                        f'min_price_{self.category_1.slug}': {'min_price': self.product1.price}})

        self.product2 = Product(name=f'Product_{self.random_number + 2}',
                                slug=f'product_{self.random_number + 2}',
                                manufacturer=self.manufacturer1,
                                price=Decimal('300.25'),
                                description='Description',
                                category=self.category_1)
        self.product2.save()

        # simulate connecting the signal with transmitter of this signal
        with patch('goods.signals.invalidate_prices_cache', autospec=True) as mocked_handler:
            post_delete.connect(mocked_handler, sender=Product)
            self.redis.srem('product_ids', self.product2.pk)
            self.product2.delete()  # action that leading to the signal send

        # number of callings of the signal must be not greater than 1
        self.assertEqual(mocked_handler.call_count, 1)
        cache_after_test = cache.get_many(f'max_price_{self.product2.category.slug}',
                                          f'min_price_{self.product2.category.slug}')
        self.assertFalse(cache_after_test)  # must be nothing

    def test_invalidate_properties_cache(self):
        """
        Checking signal, that invalidates cache for storage with queryset with product properties,
        when create or delete the product property or product category
        """
        cache.set(f'category_{self.category_1.slug}_props', [self.property1])  # initial cache value

        # calling the signal while creating new property
        with patch('goods.signals.invalidate_properties_cache', autospec=True) as mocked_handler:
            post_save.connect(mocked_handler, sender=Property)
            self.property2 = Property(name='Diagonal',
                                      numeric_value=Decimal('15.6'),
                                      category_property=self.property_category,
                                      product=self.product1)
            self.property2.save()
        # number of callings of the signal must be not greater than 1
        self.assertEqual(mocked_handler.call_count, 1)
        cache_after_test = cache.get(f'category_{self.category_1.slug}_props')
        self.assertIsNone(cache_after_test)  # must be empty value

        cache.set(f'category_{self.category_1.slug}_props', [self.property2])  # initial cache value

        # calling the signal while deleting property
        with patch('goods.signals.invalidate_properties_cache', autospec=True) as mocked_handler:
            post_delete.connect(mocked_handler, sender=Property)
            self.property1.delete()

        # number of callings of the signal must be not greater than 1
        self.assertEqual(mocked_handler.call_count, 1)
        cache_after_test = cache.get(f'category_{self.category_1.slug}_props')
        self.assertIsNone(cache_after_test)  # must be empty value

        cache.set(f'category_{self.category_1.slug}_props', [self.property1])

        # calling the signal while deleting product category
        with patch('goods.signals.invalidate_properties_cache', autospec=True) as mocked_handler:
            post_delete.connect(mocked_handler, sender=Category)
            self.category_1.delete()

        # number of callings of the signal must be not greater than 1
        self.assertEqual(mocked_handler.call_count, 1)
        cache_after_test = cache.get(f'category_{self.category_1.slug}_props')
        self.assertIsNone(cache_after_test)  # must be empty value

    def test_delete_product_images_folder(self):
        """
        Checking signal, which removes product image from AWS Bucket,
        removes directory with product photos from media root, and deleting product id from Redis
        """
        self.redis.sadd('products_ids', self.product1.pk)
        product_id = self.product1.pk  # save product id, that to be removed

        with patch('goods.signals.delete_product_images_folder', autospec=True) as mocked_handler:
            post_delete.connect(mocked_handler, sender=Product)
            self.product1.delete()

        # number of callings of the signal must be not greater than 1
        self.assertEqual(mocked_handler.call_count, 1)
        self.assertFalse(self.redis.sismember('products_ids', product_id))  # must be no product id in redis set
        self.assertNotIn(f'product_{self.product1.name}',
                         os.listdir(os.path.join(settings.MEDIA_ROOT, 'products/')))

    def tearDown(self) -> None:
        try:
            # deleting product directory from media root
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))
        except (FileNotFoundError, AttributeError):
            pass
