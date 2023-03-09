from django.test import TestCase
from django.shortcuts import reverse
from cart.cart import Cart
from goods.models import Product, Category, Manufacturer
from decimal import Decimal
from django.test.client import Client, RequestFactory


class PaymentTest(TestCase):  # TODO
    """
    Тестирование оплаты заказа
    """

    def setUp(self) -> None:
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

    def test_add_to_cart(self):
        """
        Добавление товара в корзину
        """
        self.cart.add(self.product1)
        self.cart.add(self.product2)

        self.assertEqual(len(self.cart.cart), 2)
