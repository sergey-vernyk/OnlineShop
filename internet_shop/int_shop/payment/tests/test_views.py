import os
import shutil
from decimal import Decimal
from random import randint
from unittest import skip

import requests
import stripe
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from rest_framework import status

from account.models import Profile
from coupons.models import Category as Coupon_Category, Coupon
from goods.models import Product, Category, Manufacturer
from orders.models import Order, OrderItem
from payment.views import create_checkout_session, create_discounts
from present_cards.models import Category as PresentCard_Category, PresentCard


class TestViewsPayment(TestCase):
    """
    Testing views for performing payment through Stripe
    """

    client = None
    product2 = None
    product1 = None
    profile = None
    order = None
    user = None
    session = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        random_number = randint(1, 50)

        cls.factory = RequestFactory()
        cls.user = User.objects.create_user(username='user', password='password', email='example@example.com')
        cls.user.set_password('password')
        profile = Profile.objects.create(user=cls.user)

        category_1 = Category.objects.create(name=f'Category_{random_number}', slug=f'category_{random_number}')
        category_2 = Category.objects.create(name=f'Category_{random_number + 1}', slug=f'category_{random_number + 1}')

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

        cls.order = Order.objects.create(first_name='Name',
                                         last_name='Surname',
                                         email='example@example.com',
                                         phone='+38 (099) 123 45 67',
                                         pay_method='Online',
                                         profile=profile)

        cls.order_item_1 = OrderItem.objects.create(order=cls.order,
                                                    product=cls.product1,
                                                    price=Decimal('120.20'),
                                                    quantity=2)

        cls.order_item_2 = OrderItem.objects.create(order=cls.order,
                                                    product=cls.product2,
                                                    price=Decimal('250.00'),
                                                    quantity=1)

    def test_create_checkout_session(self):
        """
        Testing creating checkout session for performing payment
        without applying discounts and with discounts
        """
        client = Client()
        session = client.session
        session.update({'order_id': self.order.pk})  # add order id into session
        session.save()

        request = self.factory.post(reverse('payment:create_checkout_session'))
        request.session = session
        request.user = self.user
        response = create_checkout_session(request)

        # total cost for goods taking into account their quantities and without discounts
        total_cost = (Decimal(self.order_item_1.price * self.order_item_1.quantity) +
                      Decimal(self.order_item_2.price * self.order_item_2.quantity)) * 100

        # redirecting to paymant page after sucessfully created checkout session
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # sucessfully loaded payment page
        self.assertEqual(requests.get(response.url).status_code, status.HTTP_200_OK)
        # getting checkout session by it id from client session
        checkout_session = stripe.checkout.Session.retrieve(request.session['stripe_checkout_session_id'])
        # total cost without discounts
        self.assertEqual(checkout_session.amount_total, total_cost)

        # add coupon to the order
        self.order.coupon = self.coupon
        self.order.save()

        response = create_checkout_session(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(requests.get(response.url).status_code, status.HTTP_200_OK)

        checkout_session = stripe.checkout.Session.retrieve(request.session['stripe_checkout_session_id'])
        amount_total_with_discount = total_cost - (total_cost * self.coupon.discount / 100)
        self.assertEqual(checkout_session.amount_total, amount_total_with_discount)

        # add present card in the order
        self.order.coupon = None
        self.order.present_card = self.card
        self.order.save()

        response = create_checkout_session(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(requests.get(response.url).status_code, status.HTTP_200_OK)

        checkout_session = stripe.checkout.Session.retrieve(request.session['stripe_checkout_session_id'])
        amount_total_with_discount = total_cost - self.card.amount * 100
        self.assertEqual(checkout_session.amount_total, amount_total_with_discount)

    def test_create_discount_success(self):
        """
        Checking sucessfully creating discount object for stripe
        """
        coupon_obj = create_discounts(discount_type='coupon', discount_value=20)
        self.assertEqual(coupon_obj.object, 'coupon')
        self.assertEqual(coupon_obj.percent_off, 20.0)
        self.assertTrue(coupon_obj.valid)

        present_card_obj = create_discounts(discount_type='present_card', discount_value=150)
        self.assertEqual(present_card_obj.object, 'coupon')
        self.assertEqual(present_card_obj.amount_off, 150 * 100)
        self.assertTrue(present_card_obj.valid)

    def test_create_discount_return_none(self):
        """
        Checking return None while creating discount object,
        when doesn't uses whatever discount in an order
        """
        coupon_obj = create_discounts()
        self.assertIsNone(coupon_obj)

    def test_payment_success(self):
        """
        Checking using correct template for page, to where
        user will follows up with successfully order complete, and
        checking context variables and their values
        """
        # creating request for check checkout session for payment
        request = self.factory.post(reverse('payment:create_checkout_session'))
        request.session = self.session
        request.user = self.user

        client = Client()
        session = client.session
        session.update({'order_id': self.order.pk})
        request.session = session

        # create checkout session
        response = create_checkout_session(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # check redirection to payment page
        # save checkout session id into client session and save this session
        session.update({'stripe_checkout_session_id': request.session['stripe_checkout_session_id']})
        session.save()
        # check whether using correct template, context variables and variables values
        resp = client.get(reverse('payment:payment_success'))
        self.assertTemplateUsed(resp, 'payment/success.html')
        self.assertIn('amount_total', resp.context)
        self.assertIn('order_id', resp.context)
        self.assertEqual(resp.context['amount_total'], Decimal('490.40'))
        self.assertEqual(resp.context['order_id'], str(self.order.pk))

    def test_payment_cancel(self):
        """
        Checking, whether using correct template for page,
        when user will follows up with not sucessfully order payment (payment was dicline)
        """
        client = Client()
        response = client.get(reverse('payment:payment_cancel'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'payment/cancel.html')

    @skip
    def test_webhook(self):  # TODO
        """
        Checking handling webhook
        """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product2.name}'))
