from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django.shortcuts import reverse
from cart.cart import Cart
from goods.models import Product, Category, Manufacturer
from decimal import Decimal


class OrderCreateTest(TestCase):  # TODO
    """
    Проверка создания заказа
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='User',
                                             password='password')

        category_phone = Category.objects.create(name='Mobile phones',
                                                 slug='mobile-phones')
        category_laptop = Category.objects.create(name='Laptops',
                                                  slug='laptops')

        manufacturer1 = Manufacturer.objects.create(name='Lenovo',
                                                    slug='lenovo',
                                                    description='Description')

        manufacturer2 = Manufacturer.objects.create(name='Huawei',
                                                    slug='huawei',
                                                    description='Description')

        self.product1 = Product.objects.create(name='Huawei Nova 5t',
                                               slug='huawei-nova-5t',
                                               manufacturer=manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category_phone)

        self.product2 = Product.objects.create(name='Lenovo ThinkBook 15',
                                               slug='lenovo-thinkbook-15',
                                               manufacturer=manufacturer2,
                                               price=Decimal('650.45'),
                                               description='Description',
                                               category=category_laptop)

        factory = RequestFactory()
        client = Client()
        session = client.session
        request = factory.get(reverse('cart:cart_detail'))
        request.session = session
        self.cart = Cart(request)

    def test_order_create(self):
        """
        Проверка создания заказа
        """
        self.cart.add(self.product1)
        self.cart.add(self.product2)

        self.client.login(username=self.user.username, password='password')
        data_order_form = {
            'first_name': 'Sergey',
            'last_name': 'Vernyk',
            'email': 'example@mail.com',
            'address': 'Address',
            'phone': '+380991234567',
            'pay_method': 'Online',
            'recipient': 'recipient',
            'comment': 'comment'
        }
        response = self.client.post(reverse('orders:order_create'), data=data_order_form)
        order_form = response.context['order_form']
        self.assertFormError(order_form({}), 'first_name', 'This field is required.')
        self.assertFormError(order_form({}), 'last_name', 'This field is required.')
        # self.assertEqual(response.status_code, 200)
