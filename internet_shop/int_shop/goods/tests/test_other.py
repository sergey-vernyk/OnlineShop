import os
import shutil

from django.test import TestCase
import redis
from django.conf import settings
from unittest.mock import patch
from goods.filters import get_max_min_price
from goods.models import Category, Manufacturer, Product
from decimal import Decimal
from random import randint
from django.core.cache import cache


class TestOtherFunctions(TestCase):
    """
    Testing other project functions
    """

    def setUp(self) -> None:
        self.random_number = randint(1, 50)

        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('common.moduls_init.redis', redis_instance)
        self.redis = redis_patcher.start()

        category_1 = Category.objects.create(name=f'Category_{self.random_number}',
                                             slug=f'category-{self.random_number}')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                    slug=f'manufacturer_{self.random_number}',
                                                    description='Description')

        manufacturer2 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number + 1}',
                                                    slug=f'manufacturer_{self.random_number + 1}',
                                                    description='Description')

        self.product1 = Product.objects.create(name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category_1)

        self.product2 = Product.objects.create(name=f'Product_{self.random_number + 1}',
                                               slug=f'product_{self.random_number + 1}',
                                               manufacturer=manufacturer2,
                                               price=Decimal('650.45'),
                                               description='Description',
                                               category=category_1)

    def test_get_max_min_price_filter(self):
        """
        Checking filter which returns maximum and minimum products price for category_slug category
        """
        # if there are no data in the cache before call the filter
        result = get_max_min_price(self.product1.category.slug)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], self.product2.price)
        self.assertEqual(result[1], self.product1.price)

        max_price = cache.get(f'max_price_{self.product1.category.slug}')
        min_price = cache.get(f'min_price_{self.product1.category.slug}')

        self.assertDictEqual(max_price, {'max_price': self.product2.price})
        self.assertDictEqual(min_price, {'min_price': self.product1.price})

        # if there are data in the cache before call the filter
        cache.set(f'max_price_{self.product1.category.slug}', {'max_price': self.product2.price})
        cache.set(f'min_price_{self.product1.category.slug}', {'min_price': self.product1.price})

        result = get_max_min_price(self.product1.category.slug)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], self.product2.price)
        self.assertEqual(result[1], self.product1.price)

        self.assertDictEqual(max_price, {'max_price': self.product2.price})
        self.assertDictEqual(min_price, {'min_price': self.product1.price})

    def tearDown(self) -> None:
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))

        cache.delete(f'max_price_{self.product1.category.slug}')
        cache.delete(f'min_price_{self.product1.category.slug}')
