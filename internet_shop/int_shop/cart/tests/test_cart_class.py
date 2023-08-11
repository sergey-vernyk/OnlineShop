import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone

from cart.cart import Cart
from coupons.models import Coupon, Category as Coupon_Category
from goods.models import Category
from goods.models import Manufacturer, Product
from present_cards.models import PresentCard, Category as PresentCard_Category


class TestCartClass(TestCase):
    """
    Checking methods logic of "cart" class
    """

    client = None
    product1 = None
    product2 = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)
        category_1 = Category.objects.create(name=f'Category_{random_number}', slug=f'category-{random_number}')
        category_2 = Category.objects.create(name=f'category_{random_number + 1}', slug=f'category_{random_number + 1}')

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
                                              category=category_card)

        cls.factory = RequestFactory()
        cls.client = Client()
        cls.session = cls.client.session

    def test_add_product_to_cart(self):
        """
        Checking adding product to cart
        """
        request = self.factory.get(reverse('goods:product_list'))
        request.session = self.session

        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)
        self.assertDictEqual(cart.cart,
                             {f'{self.product1.pk}': {'price': '300.25', 'quantity': 2},
                              f'{self.product2.pk}': {'price': '650.45', 'quantity': 1}})
        cart.add(self.product2, 2)
        self.assertDictEqual(cart.cart,
                             {f'{self.product1.pk}': {'price': '300.25', 'quantity': 2},
                              f'{self.product2.pk}': {'price': '650.45', 'quantity': 2}})

    def test_amount_count_products_in_the_cart(self):
        """
        Checking products count, considering their quantity
        """
        request = self.factory.get(reverse('goods:product_list'))
        request.session = self.session

        # create cart instance and add two products to it
        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        self.assertEqual(len(cart), 3)

    def test_getting_cart_items(self):
        """
        Checking getting cart items with their values using generator object
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        request.session = self.session

        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        # create iterator and get two items from generator object
        cart_iter = iter(cart)
        item1 = next(cart_iter)
        item2 = next(cart_iter)
        item1_items = item1.items()

        # checking items and their values in the cart dictionary
        self.assertIn(('price', Decimal('300.25')), item1_items)
        self.assertIn(('quantity', 2), item1_items)
        self.assertIn('quantity_form', item1.keys())
        self.assertIn(('product', self.product1), item1_items)
        self.assertIn(('total_price', Decimal('600.50')), item1_items)

        item2_items = item2.items()
        self.assertIn(('price', Decimal('650.45')), item2_items)
        self.assertIn(('quantity', 1), item2_items)
        self.assertIn('quantity_form', item2.keys())
        self.assertIn(('product', self.product2), item2_items)
        self.assertIn(('total_price', Decimal('650.45')), item2_items)

    def test_remove_product_from_cart(self):
        """
        Checking removing product from cart
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        request.session = self.session

        cart = Cart(request)
        # at first added two products to the cart
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        # delete products and check
        cart.remove(self.product1.pk)
        self.assertEqual(len(cart), 1)

        cart.remove(self.product2.pk)
        self.assertEqual(len(cart), 0)

    def test_clear_cart(self):
        """
        Checking the complete emptying of the cart (actually session keys) with a coupon or present card inside
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        self.session.update({'coupon_id': self.coupon.pk})
        self.session.save()
        request.session = self.session

        # create cart instance and add two product into it
        # creation comes from the session dict
        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        # cart and coupon_id must contain in the session
        self.assertIn('cart', self.session)
        self.assertIn('coupon_id', self.session)

        self.assertEqual(len(cart), 3)
        cart.clear()

        # cart and coupon_id must not contain in the session
        self.assertNotIn('cart', self.session)
        self.assertNotIn('coupon_id', self.session)

        cart = Cart(request)
        self.assertEqual(len(cart), 0)  # cart must not contain any products inside

    def test_get_total_price(self):
        """
        Checking correct total price calculation of all products in the cart with their quantities
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        request.session = self.session

        # create cart instance and add two product into it
        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        expected_total_price = self.product1.price * 2 + self.product2.price * 1
        result_total_price = cart.get_total_price()
        self.assertEqual(result_total_price, expected_total_price)

    def test_amount_items_in_cart(self):
        """
        Checking correct calculation amount different items in the cart
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        request.session = self.session

        # create cart instance and add two product into it
        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        result_total_amount = cart.get_amount_items_in()
        self.assertEqual(result_total_amount, 2)

    def test_get_total_price_with_discounts(self):
        """
        Checking correct calculation total price of products inside cart,
        when some discount have been applied
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        self.session.update({'coupon_id': self.coupon.pk})
        self.session.save()
        request.session = self.session

        # create cart instance and add two product into it
        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        price_without_discount = self.product1.price * 2 + self.product2.price * 1

        # price with coupon discount
        expected_total_price = price_without_discount - (price_without_discount * (self.coupon.discount / Decimal(100)))
        result_total_price = cart.get_total_price_with_discounts()
        self.assertEqual(result_total_price, expected_total_price)

        # price with present card amount
        self.session.update({'coupon_id': None, 'present_card_id': self.card.pk, 'cart': None})
        self.session.save()
        request.session = self.session

        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)
        expected_total_price = price_without_discount - self.card.amount
        result_total_price = cart.get_total_price_with_discounts()
        self.assertEqual(result_total_price, expected_total_price)

    def test_get_total_discount_if_using_coupon(self):
        """
        Checking correct calculation total discount
        """
        request = self.factory.get(reverse('cart:cart_detail'))  # make request for cart detail page
        self.session.update({'coupon_id': self.coupon.pk})
        self.session.save()
        request.session = self.session

        # create cart instance and add two product into it
        cart = Cart(request)
        cart.add(self.product1, 2)
        cart.add(self.product2, 1)

        price_without_discount = self.product1.price * 2 + self.product2.price * 1

        expected_amount_discount = price_without_discount * (self.coupon.discount / Decimal('100'))
        result_amount_discount = cart.get_total_discount()
        self.assertEqual(result_amount_discount, expected_amount_discount)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product2.name}'))
