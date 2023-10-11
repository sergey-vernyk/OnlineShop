import os
import shutil
from datetime import datetime
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, APIRequestFactory

from account.models import Profile
from cart.api.serializers import CartSerializer
from cart.cart import Cart
from goods.models import Product, Category, Manufacturer
from orders.api.serializers import OrderSerializer, DeliverySerializer
from orders.api.views import OrderViewSet
from orders.models import Order, Delivery


class TestOrdersAPI(APITestCase):
    """
    Testing API in orders application
    """

    def setUp(self):
        self.random_number = randint(1, 50)
        self.user = User.objects.create_user(username='testuser',
                                             password='password',
                                             email='example@example.com')
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
                                          delivery=self.delivery)

        self.client = APIClient()
        self.factory = APIRequestFactory()

    def test_get_orders_list_only_by_staff_users(self):
        """
        Checking get all orders by only staff users
        """

        response = self.client.get(reverse('orders_api:order-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # user is no staff
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('orders_api:order-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('orders_api:order-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = OrderSerializer(instance=self.order)
        view = response.renderer_context['view']
        actual_result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(view, 'pagination_class') else response.data
        expected_result = serializer.data

        self.assertEqual(actual_result[0], expected_result)
        self.assertEqual(len(actual_result), 1)

    def test_retrieve_order(self):
        """
        Checking retrieve order with id.
        Order can be retrieved by its id only by staff users.
        """
        # user is no staff
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('orders_api:order-detail',
                                           kwargs={'pk': self.order.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('orders_api:order-detail',
                                           kwargs={'pk': self.order.pk, 'version': 'v1'}))

        serializer = OrderSerializer(instance=self.order)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_order(self):
        """
        Checking create order by only authenticated users
        """
        order_data = {
            'first_name': 'Name',
            'last_name': 'Surname',
            'email': 'example@example.com',
            'phone': '+38 (066) 123 45 67',
            'pay_method': 'Online',
            'comment': 'Some comment',
            'call_confirm': False,
            'profile': self.profile.pk,

            'delivery': {
                'first_name': 'Name2',
                'last_name': 'Surname2',
                'service': 'New Post',
                'method': 'Post office',
                'office_number': '2',
                'delivery_date': datetime.strftime(
                    datetime.now().date() + timezone.timedelta(days=3), '%Y-%m-%d')
            },
        }

        # user will be not authenticated
        request = self.factory.post(reverse('orders_api:order-list', kwargs={'version': 'v1'}),
                                    data=order_data,
                                    format='json')
        request.session = self.client.session
        cart = Cart(request)
        cart.add(self.product1)
        cart.add(self.product2, 3)

        view_instance = OrderViewSet.as_view({'post': 'create'})
        response = view_instance(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # user will be authenticated
        request = self.factory.post(reverse('orders_api:order-list', kwargs={'version': 'v1'}),
                                    data=order_data,
                                    format='json', **{'HTTP_AUTHORIZATION': f'Token {self.token.key}'})
        request.session = self.client.session
        cart = Cart(request)
        cart.add(self.product1)
        cart.add(self.product2, 3)
        cart_serializer = CartSerializer(instance=[item for item in cart], many=True)

        view_instance = OrderViewSet.as_view({'post': 'create'})
        response = view_instance(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_order = Order.objects.filter(phone=order_data['phone']).exists()
        self.assertTrue(created_order)
        for field, value in Order.objects.get(phone=order_data['phone']).__dict__.items():
            if field in order_data:
                self.assertEqual(value, order_data[field])

        self.assertEqual(response.data['items'], cart_serializer.data)

    def test_partial_update_order_only_by_staff_users(self):
        """
        Checking update several order's fields only by staff users
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')  # user is not staff
        new_order_data = {
            'delivery': {
                'first_name': 'John',
                'last_name': 'Doe',
            },
            'phone': '+380677772255',
            'pay_method': 'On delivery'
        }

        response = self.client.patch(reverse('orders_api:order-detail',
                                             kwargs={'pk': self.order.pk, 'version': 'v1'}),
                                     data=new_order_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.patch(reverse('orders_api:order-detail',
                                             kwargs={'pk': self.order.pk, 'version': 'v1'}),
                                     data=new_order_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()

        for field, value in self.order.__dict__.items():
            if field in new_order_data:
                self.assertEqual(value, new_order_data[field])

        self.order.delivery.refresh_from_db()
        for field, value in self.order.delivery.__dict__.items():
            if field in new_order_data['delivery']:
                self.assertEqual(value, new_order_data['delivery'][field])

    def test_delete_order_only_by_staff_user(self):
        """
        Checking delete order with id only by staff users
        """
        # user in not staff
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.delete(reverse('orders_api:order-detail',
                                              kwargs={'pk': self.order.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user in staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.delete(reverse('orders_api:order-detail',
                                              kwargs={'pk': self.order.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(ObjectDoesNotExist):
            self.order.refresh_from_db()

    def test_get_orders_by_user(self):
        """
        Checking get all orders of current authenticated user
        """
        delivery2 = Delivery.objects.create(first_name='Some',
                                            last_name='Person',
                                            service='Ukrpost',
                                            method='Post office',
                                            office_number='5',
                                            delivery_date=datetime.strftime(
                                                datetime.now().date() + timezone.timedelta(days=5), '%Y-%m-%d'))
        # create yet another order for current user
        order2 = Order.objects.create(first_name='First',
                                      last_name='Last',
                                      email='another@example.com',
                                      phone='+38 (095) 123 22 67',
                                      pay_method='Online',
                                      profile=self.profile,
                                      delivery=delivery2)
        # user is not authenticated
        response = self.client.get(reverse('orders_api:order-orders_by_user', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # authenticate user
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('orders_api:order-orders_by_user', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = OrderSerializer(instance=[order2, self.order], many=True)
        # remove delivery data from response result
        serializer.data[0].pop('delivery')
        serializer.data[1].pop('delivery')
        self.assertEqual(response.data, serializer.data)

    def test_get_deliveries_list_only_by_staff_users(self):
        """
        Checking get all deliveries by only staff users
        """
        # create yet another delivery
        delivery2 = Delivery.objects.create(first_name='Some',
                                            last_name='Person',
                                            service='Ukrpost',
                                            method='Post office',
                                            office_number='5',
                                            delivery_date=datetime.strftime(
                                                datetime.now().date() + timezone.timedelta(days=5), '%Y-%m-%d'))

        response = self.client.get(reverse('orders_api:delivery-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # user is no staff
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('orders_api:delivery-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('orders_api:delivery-list', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = DeliverySerializer(instance=[self.delivery, delivery2], many=True)
        view = response.renderer_context['view']
        actual_result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(view, 'pagination_class') else response.data
        expected_result = serializer.data

        self.assertEqual(actual_result, expected_result)
        self.assertEqual(len(actual_result), 2)

    def test_retrieve_delivery(self):
        """
        Checking retrieve delivery with id.
        Delivery can be retrieved by its id only by staff users.
        """
        # user is no staff
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('orders_api:delivery-detail',
                                           kwargs={'pk': self.delivery.pk, 'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('orders_api:delivery-detail',
                                           kwargs={'pk': self.delivery.pk, 'version': 'v1'}))

        serializer = DeliverySerializer(instance=self.delivery)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_partial_update_delivery_only_by_staff_users(self):
        """
        Checking update several delivery's fields only by staff users
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')  # user is not staff

        new_delivery_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'office_number': 5
        }

        response = self.client.patch(reverse('orders_api:delivery-detail',
                                             kwargs={'pk': self.delivery.pk, 'version': 'v1'}),
                                     data=new_delivery_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # user is staff
        self.user.is_staff = True
        self.user.save()
        response = self.client.patch(reverse('orders_api:delivery-detail',
                                             kwargs={'pk': self.delivery.pk, 'version': 'v1'}),
                                     data=new_delivery_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.delivery.refresh_from_db()

        for field, value in self.delivery.__dict__.items():
            if field in new_delivery_data:
                self.assertEqual(value, new_delivery_data[field])

    def get_deliveries_by_user(self):
        """
        Checking get all deliveries of current authenticated user
        """
        delivery2 = Delivery.objects.create(first_name='Some',
                                            last_name='Person',
                                            service='Ukrpost',
                                            method='Post office',
                                            office_number='5',
                                            delivery_date=datetime.strftime(
                                                datetime.now().date() + timezone.timedelta(days=5), '%Y-%m-%d'))

        # create yet another order for current user in order to link delivery to user
        Order.objects.create(first_name='First',
                             last_name='Last',
                             email='another@example.com',
                             phone='+38 (095) 123 22 67',
                             pay_method='Online',
                             profile=self.profile,
                             delivery=delivery2)

        # user is not authenticated
        response = self.client.get(reverse('orders_api:delivery-deliveries_by_user', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # authenticate user
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('orders_api:delivery-deliveries_by_user', kwargs={'version': 'v1'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = DeliverySerializer(instance=[self.delivery, delivery2], many=True)
        self.assertEqual(response.data, serializer.data)

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2}'))
