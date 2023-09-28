import json
import os
import shutil
from decimal import Decimal
from random import randint
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from goods.api.serializers import ProductSerializer
from goods.models import Product, Category, Manufacturer


class TestGoodsProductAPI(APITestCase):
    """
    Testing whether we can retrieve, create, update, partial update, delete product using API
    """

    def setUp(self) -> None:
        self.random_number = randint(1, 50)
        self.user = User.objects.create_user(username='testuser', password='password')
        self.user.is_staff = True
        self.user.set_password('password')
        self.user.save()

        token = Token.objects.get(user__username=self.user.username)

        category_1 = Category.objects.create(name=f'Category_{self.random_number}',
                                             slug=f'category-{self.random_number}')
        category_2 = Category.objects.create(name=f'category_{self.random_number + 1}',
                                             slug=f'category-{self.random_number + 1}')

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
                                               category=category_2)

        self.product3 = Product.objects.create(name=f'Product_{self.random_number + 2}',
                                               slug=f'product_{self.random_number + 2}',
                                               manufacturer=manufacturer1,
                                               price=Decimal('200.00'),
                                               description='Description',
                                               category=category_2)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')  # authenticate user using Token

    def test_get_products(self):
        """
        Check obtain list of products using GET response
        """
        serializer = ProductSerializer(instance=[self.product1, self.product2, self.product3], many=True)
        response = self.client.get(reverse('goods_api:product-list'), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # results may be different, when used pagination
        result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(serializer, 'pagination_class') else response.data
        self.assertEqual(serializer.data, result)

    def test_get_products_if_passed_category(self):
        """
        Check obtain list of products using GET response if was passed category
        """
        serializer = ProductSerializer(instance=[self.product2, self.product3], many=True)
        response = self.client.get(f"{reverse('goods_api:product-list')}?slug={self.product2.category.slug}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # results may be different, when used pagination
        result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(serializer, 'pagination_class') else response.data
        self.assertEqual(json.dumps(serializer.data), json.dumps(result))

    def test_get_new_products_action(self):
        """
        Check action, which allows to get new products on the site
        """
        # make product as not new on the site
        # created date must be greater than or equal 2 weeks
        product_created_data = self.product3.created
        self.product3.created = product_created_data - timezone.timedelta(weeks=3)
        self.product3.save()

        serializer = ProductSerializer(instance=[self.product1, self.product2], many=True)
        response = self.client.get(reverse('goods_api:product-get-new-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(serializer, 'pagination_class') else response.data
        self.assertEqual(serializer.data, result)

    def test_get_promotional_products_action(self):
        """
        Check action, which allows to get promotional products on the site
        """
        # make product as promotional
        self.product3.promotional = True
        self.product3.save()

        serializer = ProductSerializer(instance=self.product3)

        response = self.client.get(reverse('goods_api:product-get-promotional-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(serializer, 'pagination_class') else response.data
        self.assertEqual(serializer.data, json.loads(json.dumps(result[0])))

    @patch('goods.utils.redis')
    @patch('goods.api.views.redis')
    def test_get_popular_products_action(self, mock_redis1, mock_redis2):
        """
        Check action, which allows to get popular products on the site
        """
        # data for "smembers" redis method
        members = {
            'products_ids': {f'{self.product1.pk}', f'{self.product2.pk}', f'{self.product3.pk}'},
        }
        # data for "hget" redis method
        views = {
            (f'product_id:{self.product1.pk}', 'views'): 10,
            (f'product_id:{self.product2.pk}', 'views'): 5,
            (f'product_id:{self.product3.pk}', 'views'): 15,
        }

        mock_redis1.smembers.side_effect = lambda key: members.get(key)
        mock_redis1.hset.return_value = 0
        mock_redis2.hget.side_effect = lambda hash_key, field: views.get((hash_key, field))

        # that expected order means, that product3 has more views than others, and product2 has lower views than other
        serializer = ProductSerializer(instance=[self.product3, self.product1, self.product2], many=True)
        response = self.client.get(reverse('goods_api:product-get-popular-products'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(serializer, 'pagination_class') else response.data
        received_result = json.loads(json.dumps(result))
        expected_result = json.loads(json.dumps(serializer.data))
        self.assertEqual(received_result, expected_result)

    def test_retrieve_product(self):
        """
        Check retrieve a product with details using GET response
        """
        serializer = ProductSerializer(instance=self.product1)
        response = self.client.get(reverse('goods_api:product-detail', args=(self.product1.pk,)))
        expected_result = json.dumps(serializer.data)
        result = json.dumps(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result, expected_result)

    def test_partial_update_product(self):
        """
        Check update few fields of the product using PATCH request
        """

        update_data = {
            'price': '1000.00',
            'rating': '3.5',
            'promotional_price': '900'
        }

        json_data_update = json.dumps(update_data)
        # user is staff by default - it can update product
        response = self.client.patch(reverse('goods_api:product-detail', args=(self.product1.pk,)),
                                     data=json_data_update,
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.price, Decimal(update_data['price']))
        self.assertEqual(self.product1.rating, Decimal(update_data['rating']))

        # user is not staff - it can't update product
        self.user.is_staff = False
        self.user.save()
        response = self.client.patch(reverse('goods_api:product-detail', args=(self.product1.pk,)),
                                     data=json_data_update,
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.user.is_staff = True
        self.user.save()

        # deleting products directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))

        # promotional price greater than default price - must be error
        update_data.update(promotional_price='1100.00')
        json_data_update = json.dumps(update_data)
        response = self.client.patch(reverse('goods_api:product-detail', args=(self.product1.pk,)),
                                     data=json_data_update,
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content),
                         {'promotional_price': ['Promotional price must not be greater than default price']})

    def test_full_update_product(self):
        """
        Check full update product using PUT request
        """

        new_product_data = {
            'category': self.product1.category.pk,
            'manufacturer': self.product1.manufacturer.pk,
            'name': 'New_prod_name',
            'slug': 'new-prod-name',
            'price': '120.00',
            'promotional': True,
            'promotional_price': '100.00',
            'rating': '3.0'
        }
        json_update_data = json.dumps(new_product_data)
        # user is staff by default - it can update product
        # deleting product directory from media root, because after update the product, it will have new name
        # and its directory will not delete after test will be complete
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))

        response = self.client.put(reverse('goods_api:product-detail', args=(self.product1.pk,)),
                                   data=json_update_data,
                                   content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.product1.refresh_from_db()
        self.assertEqual(new_product_data['name'], self.product1.name)
        self.assertEqual(new_product_data['slug'], self.product1.slug)
        self.assertEqual(Decimal(new_product_data['price']), self.product1.price)
        self.assertTrue(new_product_data['promotional'])
        self.assertEqual(Decimal(new_product_data['promotional_price']), self.product1.promotional_price)
        self.assertEqual(Decimal(new_product_data['rating']), self.product1.rating)

        # user is not staff - it can't update product
        self.user.is_staff = False
        self.user.save()
        response = self.client.put(reverse('goods_api:product-detail', args=(self.product1.pk,)),
                                   data=json_update_data,
                                   content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))

    def test_create_product(self):
        """
        Check creating product using POST request
        """
        product_data = {
            'category': self.product1.category.pk,
            'manufacturer': self.product1.manufacturer.pk,
            'name': 'Prod_name',
            'slug': 'prod-name',
            'price': '500.50',
            'promotional': False,
            'promotional_price': '0.00',
            'rating': '3.0'
        }
        json_data = json.dumps(product_data)

        # user is staff by default - it can create product
        response = self.client.post(reverse('goods_api:product-list'),
                                    data=json_data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_product = Product.objects.get(name=product_data['name'])
        self.assertEqual(new_product.name, product_data['name'])
        self.assertEqual(new_product.slug, product_data['slug'])
        self.assertEqual(new_product.price, Decimal(product_data['price']))
        self.assertFalse(new_product.promotional)
        self.assertEqual(new_product.promotional_price, Decimal(product_data['promotional_price'])),
        self.assertEqual(new_product.rating, Decimal(product_data['rating']))

        # user is not staff - it can't create product
        self.user.is_staff = False
        self.user.save()
        response = self.client.post(reverse('goods_api:product-list'),
                                    data=json_data,
                                    content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{product_data["name"]}'))

    def test_delete_product(self):
        """
        Check removing product from db using DELETE request
        """
        # user is staff by default - it can delete product
        response = self.client.delete(reverse('goods_api:product-detail', args=(self.product2.pk,)))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product2.pk).exists())

        # user is not staff - it can't delete product
        self.user.is_staff = False
        self.user.save()
        response = self.client.delete(reverse('goods_api:product-detail', args=(self.product2.pk,)))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        # deleting products directory from media root
        for name in (self.product1.name, self.product2.name, self.product3.name):
            try:
                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{name}'))
            except FileNotFoundError:
                continue
