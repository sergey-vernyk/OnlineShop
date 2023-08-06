from unittest import skip

from django.test import TestCase, RequestFactory, Client

from account.models import Profile
from orders.models import Order, OrderItem
from goods.models import Product, Category, Manufacturer
from coupons.models import Category as Coupon_Category, Coupon
from present_cards.models import Category as PresentCard_Category, PresentCard
from django.contrib.auth.models import User
from payment.views import create_checkout_session, create_discounts
from decimal import Decimal
import requests
import stripe
from rest_framework import status
from django.utils import timezone
from django.shortcuts import reverse
from random import randint


class TestViewsPayment(TestCase):
    """
    Проверка views для осуществления платежа через Stripe
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
        Проверка создания checkout сессии для оплаты
        без применения скидок и с их применением
        """
        client = Client()
        session = client.session
        session.update({'order_id': self.order.pk})  # добавление в сессию id заказа
        session.save()

        request = self.factory.post(reverse('payment:create_checkout_session'))
        request.session = session
        request.user = self.user
        response = create_checkout_session(request)

        # общая сумма за товары без скидки с учетом их кол-ва
        total_cost = (Decimal(self.order_item_1.price * self.order_item_1.quantity) +
                      Decimal(self.order_item_2.price * self.order_item_2.quantity)) * 100

        # переадресация на страницу оплаты после успешно созданной сессии
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # успешная загрузка страницы оплаты
        self.assertEqual(requests.get(response.url).status_code, status.HTTP_200_OK)
        # получение checkout сессии по ее id из сессии клиента
        checkout_session = stripe.checkout.Session.retrieve(request.session['stripe_checkout_session_id'])
        # общая стоимость без скидок
        self.assertEqual(checkout_session.amount_total, total_cost)

        # добавление купона в заказ
        self.order.coupon = self.coupon
        self.order.save()

        response = create_checkout_session(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(requests.get(response.url).status_code, status.HTTP_200_OK)

        checkout_session = stripe.checkout.Session.retrieve(request.session['stripe_checkout_session_id'])
        amount_total_with_discount = total_cost - (total_cost * self.coupon.discount / 100)
        self.assertEqual(checkout_session.amount_total, amount_total_with_discount)

        # добавление подарочной карты в заказ
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
        Проверка успешного создания объекта скидки для stripe
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
        Проверка возврата None при создании объекта скидки,
        когда в заказе не используется какая-либо из скидок
        """
        coupon_obj = create_discounts()
        self.assertIsNone(coupon_obj)

    def test_payment_success(self):
        """
        Проверка использования правильного шаблона для страницы,
        куда пользователь переходит после успешной оплаты заказа
        и проверка переменных контекста и их значения
        """
        # создание запроса для проверки создания checkout сессии для оплаты
        request = self.factory.post(reverse('payment:create_checkout_session'))
        request.session = self.session
        request.user = self.user

        client = Client()
        session = client.session
        session.update({'order_id': self.order.pk})
        request.session = session

        # создание checkout сессии
        response = create_checkout_session(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # проверка переадресации на страницу с оплатой

        # сохранение id stripe сессии в сессии клиента и сохранение последней
        session.update({'stripe_checkout_session_id': request.session['stripe_checkout_session_id']})
        session.save()

        # проверка использование правильного шаблона, переменных контекста и значение последних
        resp = client.get(reverse('payment:payment_success'))
        self.assertTemplateUsed(resp, 'payment/success.html')
        self.assertIn('amount_total', resp.context)
        self.assertIn('order_id', resp.context)
        self.assertEqual(resp.context['amount_total'], Decimal('490.40'))
        self.assertEqual(resp.context['order_id'], str(self.order.pk))

    def test_payment_cancel(self):
        """
        Проверка использования правильного шаблона для страницы,
        куда пользователь переходит после неудачной оплаты заказа (оплата была отклонена)
        """
        client = Client()
        response = client.get(reverse('payment:payment_cancel'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'payment/cancel.html')

    @skip
    def test_webhook(self):  # TODO
        """
        Проверка обработки вебхука
        """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
