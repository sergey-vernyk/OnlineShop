import os
import shutil
from datetime import datetime
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from rest_framework import status

from account.models import Profile
from cart.cart import Cart
from coupons.models import Category as Coupon_Category
from coupons.models import Coupon
from goods.models import Product, Category, Manufacturer
from orders.models import Order, OrderItem
from orders.views import OrderCreateView
from present_cards.models import Category as PresentCard_Category
from present_cards.models import PresentCard


class OrderCreateTest(TestCase):
    """
    Creating order testing
    """

    profile = None
    order_create_view = None
    request = None
    user = None
    product1 = None
    product2 = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # doing celery task locally, not sent it to the message broker
        settings.CELERY_TASK_ALWAYS_EAGER = True
        random_number = randint(1, 50)

        cls.user = User.objects.create_user(username='User', password='password')
        cls.profile = Profile.objects.create(user=cls.user)

        category_1 = Category.objects.create(name='Category1', slug='category1')
        category_2 = Category.objects.create(name='category2', slug='category2')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                    slug=f'manufacturer_{random_number}',
                                                    description='Description')

        manufacturer2 = Manufacturer.objects.create(name=f'Manufacturer_{random_number + 1}',
                                                    slug=f'manufacturer_{random_number + 1}',
                                                    description='Description')

        cls.product1 = Product.objects.create(name=f'Product_{random_number}',
                                              slug=f'product_{random_number}',
                                              manufacturer=manufacturer1,
                                              price=Decimal('300.25'),
                                              description='Description',
                                              category=category_1)

        cls.product2 = Product.objects.create(name=f'Product_{random_number + 1}',
                                              slug=f'product_{random_number + 1}',
                                              manufacturer=manufacturer2,
                                              price=Decimal('650.45'),
                                              description='Description',
                                              category=category_2)

        category_coupon = Coupon_Category.objects.create(name='For men', slug='for-men')

        cls.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                           valid_from=timezone.now(),
                                           valid_to=timezone.now() + timezone.timedelta(days=10),
                                           discount=20,
                                           category=category_coupon)

        category_card = PresentCard_Category.objects.create(name='For men', slug='for-men')

        cls.card = PresentCard.objects.create(code=f'card_code_{random_number + 5}',
                                              valid_from=timezone.now(),
                                              valid_to=timezone.now() + timezone.timedelta(days=10),
                                              amount=250,
                                              from_name='From Name',
                                              from_email='email@example.com',
                                              to_name='To Name',
                                              to_email='example_2@example.com',
                                              category=category_card,
                                              profile=cls.profile)

        factory = RequestFactory()
        client = Client()
        cls.request = factory.get(reverse('cart:cart_detail'))
        cls.request.session = client.session
        cls.request.user = cls.user
        cls.cart = Cart(cls.request)
        # creating view instance and install request attribute for it
        cls.order_create_view = OrderCreateView()
        cls.order_create_view.setup(cls.request)

    def test_order_create_correct_filled_all_fields(self):
        """
        Checking creating an order, when all fields are filled correctly
        """

        self.cart.add(self.product1)
        self.cart.add(self.product2)

        self.client.login(username=self.user.username, password='password')
        data_order_form = {
            'order_form-first_name': 'Name',
            'order_form-last_name': 'Surname',
            'order_form-email': 'example@mail.com',
            'order_form-address': 'Address',
            'order_form-phone': '+38 (099) 123 45 67',
            'order_form-pay_method': 'Online',
            'order_form-comment': 'Some comment',
            'order_form-call_confirm': True,

            'delivery_form-first_name': 'Name2',
            'delivery_form-last_name': 'Surname2',
            'delivery_form-service': 'New Post',
            'delivery_form-method': 'Self-delivery',
            'delivery_form-office_number': '1',
            'delivery_form-delivery_date': datetime.strftime(
                datetime.now().date() + timezone.timedelta(days=3), '%d-%m-%Y'
            )
        }

        response = self.client.post(reverse('orders:order_create'), data=data_order_form)
        # redirecting to the page with info about created order
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, reverse('orders:order_created'))

    def test_order_create_fields_empty(self):
        """
        Checking creating order, when not all fields are filled
        """

        self.cart.add(self.product1)
        self.cart.add(self.product2)

        fields = ('order_form-first_name', 'order_form-last_name', 'order_form-email', 'order_form-phone',
                  'order_form-pay_method', 'order_form-address', 'order_form-comment', 'order_form-call_confirm',
                  'delivery_form-first_name', 'delivery_form-last_name', 'delivery_form-service',
                  'delivery_form-method', 'delivery_form-office_number', 'delivery_form-delivery_date')

        self.client.login(username=self.user.username, password='password')
        response = self.client.post(reverse('orders:order_create'))

        order_form = response.context['form']
        delivery_form = response.context['delivery_form']

        for num, field in enumerate(fields, 1):
            # fields, which must be fill
            if field.startswith('order_form') and num < 6:
                self.assertFormError(order_form, field.split('-')[1], 'This field must not be empty')
            # fields, which may be left blank
            if field.startswith('order_form') and num > 5:
                self.assertFormError(order_form, field.split('-')[1], [])
            # fields, which must be fill
            if field.startswith('delivery_form') and num in (9, 10, 12, 14):
                self.assertFormError(delivery_form, field.split('-')[1], 'This field must not be empty')
            # fields, which may be left blank
            if field.startswith('delivery_form') and num in (11, 13):
                self.assertFormError(delivery_form, field.split('-')[1], [])

        self.assertEqual(response.status_code, status.HTTP_200_OK)  # download page with form(s) errors

    def test_create_order_items_from_cart(self):
        """
        Checking creating order items from cart elements
        """

        self.cart.add(self.product1)
        self.cart.add(self.product2)

        order = Order.objects.create(first_name='Name',
                                     last_name='Surname',
                                     email='example@example.com',
                                     phone='+38 (099) 123 45 67',
                                     pay_method='Online',
                                     profile=self.profile)

        self.order_create_view.create_order_items_from_cart(order)  # testing function call
        # function must delete from session after it will be executed
        self.assertEqual('cart' in self.request.session, False)

        # checking quantity order items and their complience after calling function
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(len(order_items), 2)
        self.assertEqual(order_items[0].product, self.product1)
        self.assertEqual(order_items[1].product, self.product2)

    def test_get_context_data(self):
        """
        Checking correct keys inside view's context
        """
        context = self.order_create_view.get_context_data()
        self.assertEqual(sorted(key for key in context), sorted(['form', 'delivery_form', 'view']))

    def test_orders_with_discounts(self):
        """
        Checking adding discount to order (coupon or present card)
        """

        data_order_form = {
            'order_form-first_name': 'Name',
            'order_form-last_name': 'Surname',
            'order_form-email': 'example@mail.com',
            'order_form-address': 'Address',
            'order_form-phone': '+38 (099) 123 45 67',
            'order_form-pay_method': 'Online',
            'order_form-comment': 'Some comment',
            'order_form-call_confirm': True,

            'delivery_form-first_name': 'Name',
            'delivery_form-last_name': 'Surname',
            'delivery_form-service': 'New Post',
            'delivery_form-method': 'Self-delivery',
            'delivery_form-office_number': '1',
            'delivery_form-delivery_date': datetime.strftime(
                datetime.now().date() + timezone.timedelta(days=3), '%d-%m-%Y'
            )
        }

        # needs own request and client for sending that request into post view's test method
        self.factory = RequestFactory()
        self.client = Client()
        # creating request, adding session and user into request
        # adding current site into request for getting domen in view
        request = self.factory.post(reverse('orders:order_create'), data=data_order_form)
        request.session = self.client.session
        request.user = self.user
        site = get_current_site(request)
        request.site = site

        discounts = {'coupon_id': self.coupon.pk, 'present_card_id': self.card.pk}

        for discount in ('coupon_id', 'present_card_id'):
            request.session.update({discount: discounts[discount]})  # adding into session coupon id or present card id
            cart = Cart(request)
            cart.add(self.product1)
            cart.add(self.product2)
            self.order_create_view.setup(request)  # set up transmitting request into all views

            self.order_create_view.post(request)  # calling POST method in view instance view
            # after successfully creating order, must be order number in the session
            self.assertTrue(request.session.get('order_id', False))
            # checking, that there are coupon or present cart into order
            order = Order.objects.get(id=request.session.get('order_id'))
            self.assertEqual((order.coupon or order.present_card).pk, discounts[discount])

    @classmethod
    def tearDownClass(cls):
        settings.CELERY_TASK_ALWAYS_EAGER = False
        super().tearDownClass()
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product2.name}'))
