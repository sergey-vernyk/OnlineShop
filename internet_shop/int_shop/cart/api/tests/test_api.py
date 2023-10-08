import json
import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from account.models import Profile
from cart.api.serializers import CartSerializer
from cart.cart import Cart
from coupons.models import Coupon, Category as CouponCategory
from goods.models import Product, Category, Manufacturer


class TestCartAPI(APITestCase):
    """
    Testing API of cart application
    """

    def setUp(self):
        random_number = randint(1, 50)
        self.user = User.objects.create_user(username='admin_user',
                                             password='password',
                                             first_name='Admin',
                                             last_name='User',
                                             email='admin@example.com')
        self.user.set_password('password')
        self.token = Token.objects.get(user__username=self.user.username)

        self.profile = Profile.objects.create(user=self.user, gender='M', about='About')

        category = Category.objects.create(name=f'Category_{random_number}', slug=f'category-{random_number}')

        manufacturer = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                   slug=f'manufacturer_{random_number}',
                                                   description='Description')

        self.product1 = Product.objects.create(name=f'Product_{random_number}',
                                               slug=f'product_{random_number}',
                                               manufacturer=manufacturer,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category)

        self.product2 = Product.objects.create(name=f'Product_{random_number + 1}',
                                               slug=f'product_{random_number + 1}',
                                               manufacturer=manufacturer,
                                               price=Decimal('100.00'),
                                               description='Description',
                                               category=category)

        category_coupon = CouponCategory.objects.create(name=f'coupon_category_{random_number + 2}',
                                                        slug=f'coupon-category-{random_number + 2}')

        self.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                            valid_from=timezone.now(),
                                            valid_to=timezone.now() + timezone.timedelta(days=10),
                                            discount=20,
                                            category=category_coupon)

        self.client = APIClient()

    def test_cart_add_or_update(self):
        """
        Checking add product to cart or update quantity of added product(s)
        """
        response = self.client.post(reverse('cart_api:add_to_cart', args=(self.product1.pk, 2)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content,
                         {'success': f'Product {self.product1.name} with id {self.product1.pk} has been successfully'
                                     f' added or updated it quantity to 2'})
        request = response.wsgi_request

        cart = Cart(request)
        self.assertEqual(len(cart), 2)
        self.assertIn(str(self.product1.pk), cart.cart)
        self.assertEqual(cart.cart[str(self.product1.pk)]['quantity'], 2)

        # update quantity of existed product in the cart
        response = self.client.post(reverse('cart_api:add_to_cart', args=(self.product1.pk, 3)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content,
                         {'success': f'Product {self.product1.name} with id {self.product1.pk} has been successfully'
                                     f' added or updated it quantity to 3'})
        request = response.wsgi_request

        cart = Cart(request)
        self.assertEqual(len(cart), 3)
        self.assertIn(str(self.product1.pk), cart.cart)
        self.assertEqual(cart.cart[str(self.product1.pk)]['quantity'], 3)

        # pass no exists product_id
        response = self.client.post(reverse('cart_api:add_to_cart', args=(999,)))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "Product with id '999' does not exist"})

    def test_cart_remove(self):
        """
        Checking remove product from the cart
        """
        # add product to cart first
        response = self.client.post(reverse('cart_api:add_to_cart', args=(self.product1.pk, 2)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request = response.wsgi_request
        cart = Cart(request)
        self.assertEqual(len(cart), 2)

        # remove product from the cart
        response = self.client.post(reverse('cart_api:remove_from_cart', args=(self.product1.pk,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request = response.wsgi_request
        cart = Cart(request)
        self.assertEqual(len(cart), 0)

    def test_cart_items(self):
        """
        Checking getting info about items in the cart with additional info
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # add one product
        response = self.client.post(reverse('cart_api:add_to_cart', args=(self.product1.pk, 2)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # add second product
        response = self.client.post(reverse('cart_api:add_to_cart', args=(self.product2.pk, 3)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request = response.wsgi_request
        request.session['coupon_id'] = self.coupon.pk
        request.session.save()

        response = self.client.get(reverse('cart_api:cart_items'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)

        serializer_data = [
            {
                'product_id': self.product1.pk,
                'product_name': self.product1.name,
                'quantity': 2,
                'price': self.product1.price
            },
            {
                'product_id': self.product2.pk,
                'product_name': self.product2.name,
                'quantity': 3,
                'price': self.product2.price

            }
        ]

        serializer = CartSerializer(data=serializer_data, many=True)

        if serializer.is_valid(raise_exception=True):
            self.assertEqual(content['items'], json.loads(json.dumps(serializer.data)))

        self.assertEqual(content['total_items'], 2)

        total_cost = self.product1.price * 2 + self.product2.price * 3
        expected_total_cost_with_discounts = (
                total_cost - (total_cost * Decimal(self.coupon.discount / 100)).quantize(Decimal('0.01'))
        )
        actual_total_cost_with_discounts = Decimal(content['total_cost_with_discounts']).quantize(Decimal('0.01'))

        expected_total_discount = total_cost * Decimal(self.coupon.discount / 100).quantize(Decimal('0.01'))
        actual_total_discount = Decimal(content['total_discount']).quantize(Decimal('0.01'))

        self.assertEqual(expected_total_cost_with_discounts, actual_total_cost_with_discounts)
        self.assertEqual(expected_total_discount, actual_total_discount)

        self.assertIn('coupon', content)
        self.assertIn('present_card', content)
        self.assertEqual(content.get('coupon'), self.coupon.pk)
        self.assertIsNone(content.get('present_card'))

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2}'))
