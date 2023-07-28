from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django.shortcuts import reverse
from rest_framework import status
from account.models import Profile
from cart.cart import Cart
from coupons.models import Coupon
from goods.models import Product, Category, Manufacturer
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from django.conf import settings

from orders.models import Order, OrderItem
from orders.views import OrderCreateView
from coupons.models import Category as Coupon_Category
from present_cards.models import Category as PresentCard_Category
from django.contrib.sites.shortcuts import get_current_site

from present_cards.models import PresentCard


class OrderCreateTest(TestCase):
    """
    Проверка создания заказа
    """

    profile = None
    order_create_view = None
    request = None
    user = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # выполнение задач celery локально, не передавая их в брокер
        settings.CELERY_TASK_ALWAYS_EAGER = True

        cls.user = User.objects.create_user(username='User', password='password')
        cls.profile = Profile.objects.create(user=cls.user)

        category_phone = Category.objects.create(name='Mobile phones', slug='mobile-phones')
        category_laptop = Category.objects.create(name='Laptops', slug='laptops')

        manufacturer1 = Manufacturer.objects.create(name='Lenovo', slug='lenovo', description='Description')

        manufacturer2 = Manufacturer.objects.create(name='Huawei', slug='huawei', description='Description')

        cls.product1 = Product.objects.create(name='Huawei Nova 5t',
                                              slug='huawei-nova-5t',
                                              manufacturer=manufacturer1,
                                              price=Decimal('300.25'),
                                              description='Description',
                                              category=category_phone)

        cls.product2 = Product.objects.create(name='Lenovo ThinkBook 15',
                                              slug='lenovo-thinkbook-15',
                                              manufacturer=manufacturer2,
                                              price=Decimal('650.45'),
                                              description='Description',
                                              category=category_laptop)

        category_coupon = Coupon_Category.objects.create(name='For men', slug='for-men')

        cls.coupon = Coupon.objects.create(code='coupon_code',
                                           valid_from=timezone.now(),
                                           valid_to=timezone.now() + timezone.timedelta(days=10),
                                           discount=20,
                                           category=category_coupon)

        category_card = PresentCard_Category.objects.create(name='For men', slug='for-men')

        cls.card = PresentCard.objects.create(code='card_code',
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
        # создание экземпляра view и установка ему атрибута request
        cls.order_create_view = OrderCreateView()
        cls.order_create_view.setup(cls.request)

    def test_order_create_correct_filled_all_fields(self):
        """
        Проверка создания заказа, когда все поля заполнены правильно
        """

        self.cart.add(self.product1)
        self.cart.add(self.product2)

        self.client.login(username=self.user.username, password='password')
        data_order_form = {
            'order_form-first_name': 'Sergey',
            'order_form-last_name': 'Vernigora',
            'order_form-email': 'example@mail.com',
            'order_form-address': 'Address',
            'order_form-phone': '+38 (099) 123 45 67',
            'order_form-pay_method': 'Online',
            'order_form-comment': 'Some comment',
            'order_form-call_confirm': True,

            'delivery_form-first_name': 'Sergey',
            'delivery_form-last_name': 'Vernyk',
            'delivery_form-service': 'New Post',
            'delivery_form-method': 'Self-delivery',
            'delivery_form-office_number': '1',
            'delivery_form-delivery_date': datetime.strftime(
                datetime.now().date() + timezone.timedelta(days=3), '%d-%m-%Y'
            )
        }

        response = self.client.post(reverse('orders:order_create'), data=data_order_form)
        # переадресация на страницу с инфо о созданном заказе
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, reverse('orders:order_created'))

    def test_order_create_fields_empty(self):
        """
        Проверка создания заказа, когда все поля не заполнены
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
            # поля, обязательные к заполнению
            if field.startswith('order_form') and num < 6:
                self.assertFormError(order_form, field.split('-')[1], 'This field must not be empty')
            # поля могут быть не заполнены
            if field.startswith('order_form') and num > 5:
                self.assertFormError(order_form, field.split('-')[1], [])
            # поля, обязательные к заполнению
            if field.startswith('delivery_form') and num in (9, 10, 12, 14):
                self.assertFormError(delivery_form, field.split('-')[1], 'This field must not be empty')
            # поля могут быть не заполнены
            if field.startswith('delivery_form') and num in (11, 13):
                self.assertFormError(delivery_form, field.split('-')[1], [])

        self.assertEqual(response.status_code, status.HTTP_200_OK)  # загрузка страницы с ошибками форм(ы)

    def test_create_order_items_from_cart(self):
        """
        Проверка создания единиц заказа из элементов в корзине
        """

        self.cart.add(self.product1)
        self.cart.add(self.product2)

        order = Order.objects.create(first_name='Name',
                                     last_name='Surname',
                                     email='example@example.com',
                                     phone='+38 (099) 123 45 67',
                                     pay_method='Online',
                                     profile=self.profile)

        self.order_create_view.create_order_items_from_cart(order)  # вызов тестовой функции
        # после выполнения функции должна удалиться корзина из сессии
        self.assertEqual('cart' in self.request.session, False)

        # созданные единицы заказа после функции, проверка их кол-ва и соответствия
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(len(order_items), 2)
        self.assertEqual(order_items[0].product, self.product1)
        self.assertEqual(order_items[1].product, self.product2)

    def test_get_context_data(self):
        """
        Проверка правильных ключей в контексте view'а
        """
        context = self.order_create_view.get_context_data()
        self.assertEqual(sorted(key for key in context), sorted(['form', 'delivery_form', 'view']))

    def test_orders_with_discounts(self):
        """
        Проверка добавления скидки на заказ (купон или подарочная карта)
        """

        data_order_form = {
            'order_form-first_name': 'Sergey',
            'order_form-last_name': 'Vernigora',
            'order_form-email': 'example@mail.com',
            'order_form-address': 'Address',
            'order_form-phone': '+38 (099) 123 45 67',
            'order_form-pay_method': 'Online',
            'order_form-comment': 'Some comment',
            'order_form-call_confirm': True,

            'delivery_form-first_name': 'Sergey',
            'delivery_form-last_name': 'Vernyk',
            'delivery_form-service': 'New Post',
            'delivery_form-method': 'Self-delivery',
            'delivery_form-office_number': '1',
            'delivery_form-delivery_date': datetime.strftime(
                datetime.now().date() + timezone.timedelta(days=3), '%d-%m-%Y'
            )
        }

        # нужен свой запрос и клиент для отправки последнего в post метод тестируемого view
        self.factory = RequestFactory()
        self.client = Client()

        # создание запроса, добавление сессии и пользователя в запрос
        # добавление текущего сайта в запрос для получения домена во view
        request = self.factory.post(reverse('orders:order_create'), data=data_order_form)
        request.session = self.client.session
        request.user = self.user
        site = get_current_site(request)
        request.site = site

        discounts = {'coupon_id': self.coupon.pk, 'present_card_id': self.card.pk}

        for discount in ('coupon_id', 'present_card_id'):
            request.session.update({discount: discounts[discount]})  # добавление в сессию id купона или карты
            cart = Cart(request)
            cart.add(self.product1)
            cart.add(self.product2)
            self.order_create_view.setup(request)  # настройка передачи request во все view's

            self.order_create_view.post(request)  # вызов метода POST в экземпляре тестируемого view
            # после успешного создания заказа в сессии должен быть номер заказа
            self.assertTrue(request.session.get('order_id', False))
            # проверка, что в заказе есть купон или карта
            order = Order.objects.get(id=request.session.get('order_id'))
            self.assertEqual((order.coupon or order.present_card).pk, discounts[discount])

    @classmethod
    def tearDownClass(cls):
        settings.CELERY_TASK_ALWAYS_EAGER = False
        super().tearDownClass()
