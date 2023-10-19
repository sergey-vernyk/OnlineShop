import json
import os
import shutil
from datetime import datetime
from decimal import Decimal
from random import randint
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase, APIClient

from account.models import Profile
from coupons.models import Category as CouponCategory
from coupons.models import Coupon
from goods.models import Product, Category, Manufacturer
from orders.models import Delivery, Order, OrderItem
from payment.api.serializers import PaymentSerializer


class MockStripeCheckoutSession:
    """
    Class for mock `stripe checkout session`.
    """

    def __init__(self, *args, **kwargs):
        """
        Actually needs only one attributes for simulate `stripe checkout session` as an object.
        It is `url`.
        """
        self.id = kwargs['id']
        self.url = kwargs['url']

    def __getitem__(self, item):
        return self.__dict__[item]


class MockStripeCoupon:
    """
    Class for mock `stripe create coupon`.
    """

    def __init__(self, *args, **kwargs):
        """
        Actually needs only two attributes for simulate `stripe create coupon` as an object.
        It is `percent_off` and `duration`.
        """
        self.id = kwargs['id']
        self.percent_off = kwargs['percent_off']
        self.duration = kwargs['duration']

    def __getitem__(self, item):
        return self.__dict__[item]


class TestPaymentAPI(APITestCase):
    """
    Testing api for payment application
    """

    def setUp(self):
        self.random_number = randint(1, 50)
        self.user = User.objects.create_user(username='testuser',
                                             password='password',
                                             email='example@example.com',
                                             first_name='Super',
                                             last_name='Admin')
        self.user.set_password('password')

        self.profile = Profile.objects.create(user=self.user)

        self.token = Token.objects.get(user__username=self.user.username)

        category = Category.objects.create(name=f'Category_{self.random_number}',
                                           slug=f'category-{self.random_number}')

        manufacturer = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                   slug=f'manufacturer_{self.random_number}',
                                                   description='Description')

        self.product1 = Product.objects.create(name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=manufacturer,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category)

        self.product2 = Product.objects.create(name=f'Product_{self.random_number + 1}',
                                               slug=f'product_{self.random_number + 1}',
                                               manufacturer=manufacturer,
                                               price=Decimal('650.45'),
                                               description='Description',
                                               category=category)

        category_coupon = CouponCategory.objects.create(name=f'coupon_category_{self.random_number + 2}',
                                                        slug=f'coupon-category-{self.random_number + 2}')

        self.coupon = Coupon.objects.create(code=f'coupon_code_{self.random_number + 5}',
                                            valid_from=timezone.now(),
                                            valid_to=timezone.now() + timezone.timedelta(days=10),
                                            discount=20,
                                            category=category_coupon)

        self.delivery = Delivery.objects.create(first_name='Name2',
                                                last_name='Surname2',
                                                service='New Post',
                                                method='Post office',
                                                office_number=2,
                                                delivery_date=datetime.strftime(
                                                    datetime.now().date() + timezone.timedelta(days=3), '%Y-%m-%d'))

        self.order = Order.objects.create(first_name='Name',
                                          last_name='Surname',
                                          email='example@example.com',
                                          phone='+38 (099) 123 45 67',
                                          pay_method='Online',
                                          profile=self.profile,
                                          delivery=self.delivery,
                                          coupon=self.coupon)

        self.order_item1 = OrderItem.objects.create(product=self.product1,
                                                    order=self.order,
                                                    quantity=2,
                                                    price=self.product1.price)

        self.order_item2 = OrderItem.objects.create(product=self.product2,
                                                    order=self.order,
                                                    quantity=1,
                                                    price=self.product2.price)

        self.client = APIClient()
        self.factory = APIRequestFactory()

    def test_make_payment_if_was_no_order(self):
        """
        Checking response, if order was not completed, e.g. no order id in session
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(reverse('payment_api:make_payment', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'You must make order first and than you will can make a payment'})

    def test_make_payment_if_order_payment_type_is_not_online(self):
        """
        Checking response, if was order, but in order info pay method type is not Online
        """
        self.order.pay_method = 'On delivery'
        self.order.save(update_fields=['pay_method'])

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # simulate, that order has been completed and order_id is in the client session
        session = self.client.session
        session.update({'order_id': self.order.pk})
        session.save()

        response = self.client.post(reverse('payment_api:make_payment', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Order pay method must be `Online` to make online payment'})

    @patch('payment.views.stripe.checkout.Session.create')
    @patch('payment.views.stripe.Coupon.create')
    def test_make_payment_success(self, mock_coupon, mock_session):
        """
        Checking make payment if all conditions have been met
        """

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # simulate, that order has been completed and order_id is in the client session
        session = self.client.session
        session.update({'order_id': self.order.pk})
        session.save()

        serializer = PaymentSerializer(data=[
            {
                'product_id': self.product1.pk,
                'quantity': 2,
                'price': self.product1.price
            },
            {
                'product_id': self.product2.pk,
                'quantity': 1,
                'price': self.product2.price
            }
        ], many=True)

        serializer_data = None
        if serializer.is_valid(raise_exception=True):
            serializer_data = json.loads(json.dumps(serializer.data))

        # create mock checkout session object from custom class
        stripe_mock_session = MockStripeCheckoutSession(
            id='cs_test_a13EMVtzPmtnq2bVLcPEKoqLPus1LUh00lrinzrwKJ88EjxRvRd6IwjXKi2jRxYkk',
            url='https://checkout.stripe.com/c/pay/cs_test_a13EMVtzPmtnq2bVLcPEKoqLPus1LUh00xRNmcjxRvRd6IwjXKi2jRx'
                'Ykk#fidkdWxOYHwnPyd1blpxYHZxWjA0SG8xaHVEZzRnY2pOPU1xcUdEanA9PDJfYzRqfE9DZ3xNcW00cTZMTG1CYmRAMjdyQ19'
        )
        mock_session.return_value = stripe_mock_session

        # create mock coupon object from custom class
        stripe_mock_coupon = MockStripeCoupon(
            id='JLQML85RVC',
            duration='forever',
            percent_off=self.coupon.discount
        )
        mock_coupon.return_value = stripe_mock_coupon

        response = self.client.post(reverse('payment_api:make_payment', kwargs={'version': 'v1'}))
        response_content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # two dict with serializer data and one dict with extra content (url, total_purchase_cost)
        self.assertEqual(len(response_content), 3)
        self.assertEqual(response_content[:-1], serializer_data)
        self.assertIn('url', response_content[-1])
        self.assertIn('total_purchase_cost', response_content[-1])
        self.assertEqual(response_content[-1]['url'], stripe_mock_session.url)
        self.assertEqual(response_content[-1]['total_purchase_cost'], 1000.76)

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2}'))
