import json
import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.http.response import JsonResponse
from django.shortcuts import reverse
from django.test import TestCase, Client
from django.utils import timezone
from rest_framework import status

from coupons.models import Category as Coupon_Category, Coupon
from goods.models import Product, Category, Manufacturer
from present_cards.models import Category as PresentCard_Category, PresentCard


class TestsCartViews(TestCase):
    """
    Testing "cart" views
    """

    product1 = None
    product2 = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)

        category_1 = Category.objects.create(name=f'Category_{random_number}', slug=f'category-{random_number}')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                    slug=f'manufacturer_{random_number}',
                                                    description='Description')

        cls.product1 = Product.objects.create(name=f'Product_{random_number}',
                                              slug=f'product_{random_number}',
                                              manufacturer=manufacturer1,
                                              price=Decimal('300.25'),
                                              description='Description',
                                              category=category_1)

        cls.product2 = Product.objects.create(name=f'Product_{random_number + 1}',
                                              slug=f'product_{random_number + 1}',
                                              manufacturer=manufacturer1,
                                              price=Decimal('100.00'),
                                              description='Description',
                                              category=category_1)

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

    def test_cart_add(self):
        """
        Checking adding products to cart, correct data and their values in JSON response contents
        """
        client = Client()
        # add AJAX header to request
        self.response = client.post(reverse('cart:cart_add'),
                                    {'product_id': self.product1.pk, 'quantity': 2},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        self.assertIsInstance(self.response, JsonResponse)  # whether received JSON response

        response_content = json.loads(self.response.content)  # convert JSON response content to python dict

        self.assertIn('cart_len', response_content)
        self.assertIn('added_prod_cost', response_content)
        self.assertIn('total_price', response_content)
        self.assertIn('total_price_discounts', response_content)
        self.assertIn('total_discount', response_content)

        self.assertEqual(response_content['cart_len'], 2)
        self.assertEqual(Decimal(response_content['added_prod_cost']), self.product1.price * 2)
        self.assertEqual(Decimal(response_content['total_price']), self.product1.price * 2)
        self.assertEqual(Decimal(response_content['total_price_discounts']), self.product1.price * 2)
        self.assertEqual(Decimal(response_content['total_discount']), 0)

    def test_cart_detail_without_applying_discounts(self):
        """
        Checking it the correct template is used, context variables,
        for detail display cart without applied discounts
        """
        client = Client()
        self.response = client.get(reverse('cart:cart_detail'))

        self.assertEqual(self.response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(self.response, 'cart/detail.html')
        self.assertIn('cart', self.response.context)
        self.assertIn('coupon_form', self.response.context)
        self.assertIn('present_card_form', self.response.context)
        # form with discount code must not fill
        self.assertEqual(self.response.context['coupon_form'].initial, {'code': ''})
        self.assertEqual(self.response.context['present_card_form'].initial, {'code': ''})

    def test_cart_detail_with_applying_discount(self):
        """
        Checking it the correct template is used, context variables,
        for detail display cart with applied one of discounts
        """
        client = Client()
        session = client.session
        session.update({'coupon_id': self.coupon.pk})
        session.save()
        # coupon was applied
        self.response = client.get(reverse('cart:cart_detail'))
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.response.context['coupon_form'].initial['code'], self.coupon.code)

        del session['coupon_id']
        session.save()
        session.update({'present_card_id': self.card.pk})
        session.save()
        # present card was applied
        self.response = client.get(reverse('cart:cart_detail'))
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.response.context['present_card_form'].initial['code'], self.card.code)

    def test_cart_remove(self):
        """
        Checking deleting products from cart, whether correct data, and it values
        contains in JSON response. After delete, there are remains one product yet
        """
        urls = {
            'previous_url': 'http://testserver'
        }

        client = Client()
        session = client.session
        # add two products to the "cart"
        session.update({'urls': urls, 'cart': {
            self.product1.pk: {'price': str(self.product1.price), 'quantity': 1},
            self.product2.pk: {'price': str(self.product2.price), 'quantity': 1}}
                        })
        session.save()

        # add AJAX header to request
        # deleting only one product
        self.response = client.post(reverse('cart:cart_remove'),
                                    {'product_id': self.product1.pk},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        self.assertIsInstance(self.response, JsonResponse)  # whether received JSON response
        response_content = json.loads(self.response.content)
        self.assertIn('cart_len', response_content)
        self.assertIn('total_price', response_content)
        self.assertIn('total_price_discounts', response_content)
        self.assertIn('total_discount', response_content)
        self.assertIn('prev_url', response_content)

        self.assertEqual(response_content['cart_len'], 1)
        self.assertEqual(Decimal(response_content['total_price']), self.product2.price)
        self.assertEqual(Decimal(response_content['total_price_discounts']), self.product2.price)
        self.assertEqual(Decimal(response_content['total_discount']), 0)
        self.assertIsNone(response_content['prev_url'])

        # deleting second the las product
        self.response = client.post(reverse('cart:cart_remove'),
                                    {'product_id': self.product2.pk},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        self.assertIsInstance(self.response, JsonResponse)  # whether received JSON response
        response_content = json.loads(self.response.content)

        self.assertEqual(response_content['cart_len'], 0)
        self.assertEqual(Decimal(response_content['total_price']), 0)
        self.assertEqual(Decimal(response_content['total_price_discounts']), 0)
        self.assertEqual(Decimal(response_content['total_discount']), 0)
        self.assertURLEqual(response_content['prev_url'], urls['previous_url'])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{cls.product2.name}'))
