import json
import os
import shutil
from decimal import Decimal
from random import randint
from unittest.mock import patch

import redis
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.db import connection
from django.db.models.signals import pre_migrate
from django.dispatch import receiver
from django.http.response import JsonResponse
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from rest_framework import status

from account.models import Profile
from cart.forms import CartQuantityForm
from goods.forms import (
    FilterByManufacturerForm,
    SortByPriceForm,
    SearchForm,
    FilterByPriceForm,
    RatingSetForm,
    CommentProductForm,
)
from goods.models import (
    Category,
    Manufacturer,
    Product,
    Favorite,
    Comment,
    Property,
    PropertyCategory
)
from goods.views import ProductListView, ProductDetailView, FilterResultsView


@receiver(signal=pre_migrate, sender=apps.get_app_config('goods'))
def app_pre_migration(sender, app_config, **kwargs):
    """
    Signal, that will create TrigramSimilarity pg_trgm extension in test postgres DB before migrations
    """
    cur = connection.cursor()
    cur.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')


class TestProductListView(TestCase):
    """
    Testing methods of the class ProductListView
    """

    def setUp(self):
        self.random_number = randint(1, 50)
        self.client = Client()
        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('goods.views.ProductListView', redis_instance)
        self.redis = redis_patcher.start()  # mock redis instance

        self.factory = RequestFactory()

        # default user
        self.user = User.objects.create_user(username='User', password='password')
        self.user.set_password('password')
        self.profile = Profile.objects.create(user=self.user)

        # guest user
        user_for_guest = User.objects.create_user(username='guest_user', password='guest_password')
        user_for_guest.set_password('guest_password')
        self.guest_profile = Profile.objects.create(user=user_for_guest)

        Favorite.objects.create(profile=self.guest_profile)

        category_1 = Category.objects.create(name=f'Category_{self.random_number}',
                                             slug=f'category-{self.random_number}')
        category_2 = Category.objects.create(name=f'category_{self.random_number + 1}',
                                             slug=f'category-{self.random_number + 1}')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                    slug=f'manufacturer_{self.random_number}',
                                                    description='Description')

        manufacturer2 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number + 1}',
                                                    slug=f'manufacturer_{self.random_number + 1}',
                                                    description='Description')

        self.product1 = Product.objects.create(name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category_1)

        self.product2 = Product.objects.create(name=f'Product_{self.random_number + 1}',
                                               slug=f'product_{self.random_number + 1}',
                                               manufacturer=manufacturer2,
                                               price=Decimal('650.45'),
                                               description='Description',
                                               category=category_2)

        Favorite.objects.create(profile=self.profile)  # favorites for default profile
        object_list = [self.product1, self.product2]  # objects for the context

        self.request = self.factory.get(reverse('goods:product_list'))
        self.request.user = self.user

        self.instance = ProductListView()
        setattr(self.instance, 'object_list', object_list)
        setattr(self.instance, 'profile', self.profile)

        self.profile.profile_favorite.product.add(self.product1)  # add product to profile's favorite

    def test_get_context_data(self):
        """
        Checking keys and values in context dict
        """
        # if category_slug and filter_price were passed
        self.instance.setup(self.request,
                            **{'category_slug': f'category-{self.random_number}', 'filter_price': ('120.20', '350.00')})
        self.request.user = self.user
        self.request.LANGUAGE_CODE = 'en'

        context = self.instance.get_context_data()
        # whether the key exists in context
        for key in ('object_list', 'products', 'category', 'filter_manufacturers', 'category_properties',
                    'manufacturers_prod_qnty', 'favorites', 'sorting_by_price', 'search_form', 'filter_price', 'place'):
            self.assertIn(key, context)

        # checking context values
        for key, value in context.items():
            if key == 'object_list':
                self.assertEqual(list(value), [self.product1, self.product2])
            elif key == 'products':
                self.assertEqual(list(value), [self.product1, self.product2])
            elif key == 'category':
                self.assertEqual(value, Category.objects.get(slug=self.instance.kwargs['category_slug']))
            elif key == 'filter_manufacturers':
                self.assertIsInstance(value, FilterByManufacturerForm)
            elif key == 'category_properties':
                self.assertEqual(value, {})
            elif key == 'manufacturers_prod_qnty':
                self.assertEqual(value, {self.product1.manufacturer.name: 1})
            elif key == 'favorites':
                self.assertEqual(list(value), [self.product1])
            elif key == 'sorting_by_price':
                self.assertIsInstance(value, SortByPriceForm)
            elif key == 'search_form':
                self.assertIsInstance(value, SearchForm)
            elif key == 'filter_price':
                self.assertIsInstance(value, FilterByPriceForm)
                self.assertEqual(value.initial, {'price_min': Decimal('120.20'), 'price_max': Decimal('350.00')})
            elif key == 'place':
                self.assertEqual(value, 'mainlist')

        # if only category_slug was passed
        self.instance.setup(self.request,
                            **{'category_slug': f'category-{self.random_number}'})
        self.request.user = self.user

        context = self.instance.get_context_data()
        # whether the key exists in context
        for key in ('object_list', 'products', 'category', 'filter_manufacturers', 'category_properties',
                    'manufacturers_prod_qnty', 'favorites', 'sorting_by_price', 'search_form', 'filter_price',
                    'place'):
            self.assertIn(key, context)

        # checking context values
        for key, value in context.items():
            if key == 'object_list':
                self.assertEqual(list(value), [self.product1, self.product2])
            elif key == 'products':
                self.assertEqual(list(value), [self.product1, self.product2])
            elif key == 'category':
                self.assertEqual(value, Category.objects.get(slug=self.instance.kwargs['category_slug']))
            elif key == 'filter_manufacturers':
                self.assertIsInstance(value, FilterByManufacturerForm)
            elif key == 'category_properties':
                self.assertEqual(value, {})
            elif key == 'manufacturers_prod_qnty':
                self.assertEqual(value, {self.product1.manufacturer.name: 1})
            elif key == 'favorites':
                self.assertEqual(list(value), [self.product1])
            elif key == 'sorting_by_price':
                self.assertIsInstance(value, SortByPriceForm)
            elif key == 'search_form':
                self.assertIsInstance(value, SearchForm)
            elif key == 'filter_price':
                self.assertIsInstance(value, FilterByPriceForm)
                # must be only price 300.25, as min and max, since it is the price of a product in one received category
                self.assertEqual(value.initial, {'price_min': Decimal('300.25'), 'price_max': Decimal('300.25')})
            elif key == 'place':
                self.assertEqual(value, 'mainlist')

    def test_get_queryset(self):
        """
        Checking queryset values
        """
        # if only category_slug was passed
        self.instance.setup(self.request, **{'category_slug': f'category-{self.random_number}'})

        queryset = self.instance.get_queryset()
        self.assertEqual(queryset.get(), self.product1)  # in the queryset must be only one product

        # if category_slug and search_result were passed
        # assume, that we've got 1 product in result_search dict after search request
        self.instance.setup(self.request, **{'category_slug': f'category-{self.random_number}',
                                             'search_result': [self.product2, ]})

        queryset = self.instance.get_queryset()
        self.assertQuerysetEqual(queryset, [self.product2, ])  # the queryset must contains 1 product

        # if kwargs not contains neither category_slug nor search_result
        self.instance.setup(self.request)
        queryset = self.instance.get_queryset()
        # the queryset must contains all products
        self.assertQuerysetEqual(sorted(list(queryset), key=lambda p: p.pk),
                                 sorted([self.product1, self.product2], key=lambda p: p.pk))

    def test_get_method(self):
        """
        Checking the get method, if there was a search request
        """

        # set number of product's views in redis
        self.redis.hset(f'product_id:{self.product1.pk}', 'views', '5')
        self.redis.hset(f'product_id:{self.product2.pk}', 'views', '10')

        # search request with "product" word
        request = self.factory.get(reverse('goods:product_list'), data={'query': 'product'})
        request.user = self.user
        self.instance.setup(request)

        self.instance.get(request)  # the GET request itself
        self.assertTrue(self.instance.kwargs.get('search_result', False))
        # instance's kwargs must contains search_result key with 2 products as the values,
        # which ordered by product's views value
        self.assertQuerysetEqual(self.instance.kwargs['search_result'], [self.product2, self.product1])

    def test__get_query_results(self):
        """
        Checking correspondence of the search results
        """
        # set number of product's views in redis
        self.redis.hset(f'product_id:{self.product1.pk}', 'views', '5')
        self.redis.hset(f'product_id:{self.product2.pk}', 'views', '10')

        # if category_slug was passed
        result = self.instance._get_query_results(query='product', category_slug=f'category-{self.random_number}')
        self.assertEqual(result[0], self.product1)  # must be found product1

        # without category_slug
        result = self.instance._get_query_results(query='product')
        # must be found 2 products; product2 actually more watched, thus it will be first in the queryset
        expected_result = [self.product2, self.product1]
        self.assertEqual(list(result), expected_result)

    def test_dispatch_method(self):
        """
        Checking whether the method sets "profile" attribute correctly
        """
        self.instance.setup(self.request)
        self.request.user = AnonymousUser()  # user is not authenticated
        self.instance.dispatch(self.request)
        self.assertEqual(self.instance.profile, self.guest_profile)  # must be a guest_user

        self.request.user = self.user  # user is authenticated
        self.instance.dispatch(self.request)
        self.assertEqual(self.instance.profile, self.profile)  # must be a default profile

    def tearDown(self):
        # deleting products directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))


class TestProductDetailView(TestCase):
    """
    Testing methods of the class ProductDetailView
    """

    def setUp(self):
        self.random_number = randint(1, 50)
        self.client = Client()
        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch(target='goods.views.redis', new=redis_instance)
        self.redis = redis_patcher.start()  # mock redis instance

        self.factory = RequestFactory()

        # default user
        self.user = User.objects.create_user(username='User',
                                             password='password',
                                             first_name='Name',
                                             last_name='Surname',
                                             email='example@example.com')
        self.user.set_password('password')
        self.profile = Profile.objects.create(id=0, user=self.user)  # id = 0 because it will be used with redis
        Favorite.objects.create(profile=self.profile)

        # guest user
        user_for_guest = User.objects.create_user(username='guest_user', password='guest_password')
        user_for_guest.set_password('guest_password')
        self.guest_profile = Profile.objects.create(user=user_for_guest)

        Favorite.objects.create(profile=self.guest_profile)

        product_category = Category.objects.create(name=f'Category_{self.random_number}',
                                                   slug=f'category-{self.random_number}')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                    slug=f'manufacturer_{self.random_number}',
                                                    description='Description')
        # id = 0 because it will be used with redis
        self.product1 = Product.objects.create(id=0,
                                               name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=product_category)

        self.comment = Comment.objects.create(product=self.product1,
                                              profile=self.profile,
                                              user_name=self.profile.user.first_name,
                                              user_email=self.profile.user.email,
                                              body='Body of comment')

        property_category = PropertyCategory.objects.create(name=f'property_category_{self.random_number}')
        # add product category to PropertyCategory instance as category, that does mean,
        # that it product category suits to that property
        self.property = Property.objects.create(name='Color',
                                                text_value='Green',
                                                category_property=property_category,
                                                product=self.product1)

        # create view instance and add to it attributes with not None values
        self.instance = ProductDetailView()
        setattr(self.instance, 'object', self.product1)
        setattr(self.instance, 'profile', self.profile)

        self.profile.profile_favorite.product.add(self.product1)  # add product to profile's favorite

    def test_get_context_data(self):
        """
        Checking keys and values in context dict
        """
        self.request = self.factory.get(reverse('goods:product_detail',
                                                args=(self.product1.pk, self.product1.slug)))
        self.request.user = self.user
        self.request.LANGUAGE_CODE = 'en'
        self.profile.comments_liked.add(self.comment)  # add to profile comment, which it rated as like

        self.instance.setup(self.request)
        context = self.instance.get_context_data()

        # whether the key exists in context
        for key in ('object', 'product', 'form', 'quantity_form', 'comment_form',
                    'comments', 'properties', 'is_in_favorite', 'profile_rated_comments'):
            self.assertIn(key, context)

        # checking context values
        for key, value in context.items():
            if key == 'object':
                self.assertEqual(value, self.product1)
            elif key == 'product':
                self.assertEqual(value, self.product1)
            elif key == 'properties':
                self.assertEqual(value.get(), self.property)
            elif key == 'is_in_favorite':
                self.assertTrue(value)
            elif key == 'profile_rated_comments':
                self.assertEqual(value, {'liked_comments': [self.comment.pk], 'unliked_comments': []})
            elif key == 'form':
                self.assertIsInstance(value, RatingSetForm)
            elif key == 'quantity_form':
                self.assertIsInstance(value, CartQuantityForm)
            elif key == 'comment_form':
                self.assertIsInstance(value, CommentProductForm)
                # whether these fields are filled, when user in authenticated
                self.assertEqual(value.fields['user_name'].initial, 'Name')
                self.assertEqual(value.fields['user_email'].initial, 'example@example.com')

    def test_is_in_favorite(self):
        """
        Checking whether product is or isn't in profile's favorite
        """
        self.request = self.factory.get(reverse('goods:product_detail',
                                                args=(self.product1.pk, self.product1.slug)))
        self.request.user = self.user
        # profile already has product1 in own favorite (installed in setUp method)
        result = self.instance.is_in_favorite()
        self.assertTrue(result)

        self.profile.profile_favorite.product.remove(self.product1)  # remove product1 from profile's favorite
        result = self.instance.is_in_favorite()
        self.assertFalse(result)

    def test_get_profile_rated_comments(self):
        """
        Checking getting dict with correct info about what comments profile had rated either as liked or disliked
        """
        self.request = self.factory.get(reverse('goods:product_detail',
                                                args=(self.product1.pk, self.product1.slug)))
        self.request.user = self.user
        self.profile.comments_liked.add(self.comment)  # rate comment as liked for profile
        result = self.instance.get_profile_rated_comments()
        expected_result = {
            'liked_comments': [self.comment.pk],
            'unliked_comments': [],
        }
        self.assertEqual(result, expected_result)

    def test_dispatch_method(self):
        """
        Checking whether the method sets "profile" attribute correctly
        """
        self.response = self.client.get(reverse('goods:product_detail',
                                                args=(self.product1.pk, self.product1.slug)))
        self.assertEqual(self.response.status_code, 200)
        request = self.response.wsgi_request

        self.instance.setup(request, **{'product_pk': self.product1.pk})  # add product_pk to the kwargs
        request.user = AnonymousUser()  # user is not authenticated
        self.instance.dispatch(request)
        self.assertEqual(self.instance.profile, self.guest_profile)  # must be a guest_user

        request.user = self.user  # user is authenticated
        self.instance.dispatch(request)
        self.assertEqual(self.instance.profile, self.profile)  # must be a default profile

    def test_get_method(self):
        """
        Checking performing the get method and variables in redis
        """
        self.client.login(username=self.user.username, password='password')  # login as default profile

        self.response = self.client.get(reverse('goods:product_detail',
                                                args=(self.product1.pk, self.product1.slug)))
        self.assertEqual(self.response.status_code, 200)

        # obtain data from redis by corresponds keys
        product_views = self.redis.hget(f'product_id:{self.product1.pk}', 'views')
        expired_time = self.redis.ttl(f'profile_id:{self.profile.pk}')
        products_viewers = self.redis.smembers(f'profile_id:{self.profile.pk}')

        self.assertEqual(product_views, '1')
        self.assertTrue(expired_time <= 604800 and expired_time != -1)  # must not be -1 (key has no expire time)
        self.assertEqual(products_viewers, set(f'{self.profile.pk}'))  # only default user "watched" the product

    def test_set_like_dislike_comment(self):
        """
        Checking setting like/dislike to comment, using AJAX request
        """
        self.client.login(username=self.user.username, password='password')  # login as default profile

        # make post request, using AJAX; send action "unlike" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'unlike'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        self.assertEqual(content_response['new_count_unlikes'], 1)
        self.assertEqual(content_response['new_count_likes'], 0)

        # make post request, using AJAX; send action "unlike" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'unlike'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        # "unlike" must be removed
        self.assertEqual(content_response['new_count_unlikes'], 0)
        self.assertEqual(content_response['new_count_likes'], 0)

        # make post request, using AJAX; send action "like" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'like'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        self.assertEqual(content_response['new_count_unlikes'], 0)
        self.assertEqual(content_response['new_count_likes'], 1)

        # make post request, using AJAX; send action "like" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'like'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        # "like" must be removed
        self.assertEqual(content_response['new_count_unlikes'], 0)
        self.assertEqual(content_response['new_count_likes'], 0)

        # make post request, using AJAX; send action "like" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'like'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        self.assertEqual(content_response['new_count_unlikes'], 0)
        self.assertEqual(content_response['new_count_likes'], 1)

        # make post request, using AJAX; send action "unlike" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'unlike'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        # "unlike" must be toggled from "like"
        self.assertEqual(content_response['new_count_unlikes'], 1)
        self.assertEqual(content_response['new_count_likes'], 0)

        # make post request, using AJAX; send action "like" for comment_id
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'comment_id': self.comment.pk, 'action': 'like'},
                                         **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)
        # "like" must be toggled from "unlike"
        self.assertEqual(content_response['new_count_unlikes'], 0)
        self.assertEqual(content_response['new_count_likes'], 1)

    def test_send_comment_about_product(self):
        """
        Checking leaving a comment about product and saving comment to DB
        """
        self.client.login(username=self.user.username, password='password')  # login as default profile

        captcha_text = 'AAA111'
        self.redis.hset(f'captcha:{captcha_text}', 'captcha_text', captcha_text)

        # make post request with all correct comment data
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'user_name': self.user.username,
                                               'user_email': self.user.email,
                                               'body': self.comment.body,
                                               'captcha': 'AAA111'})
        # must be redirection to the same page
        self.assertRedirects(self.response, reverse('goods:product_detail',
                                                    args=(self.product1.pk, self.product1.slug)))

        # make post request when not all fields are filled
        self.response = self.client.post(reverse('goods:product_detail',
                                                 args=(self.product1.pk, self.product1.slug)),
                                         data={'user_name': self.user.username,
                                               'user_email': self.user.email,
                                               'body': '',
                                               'captcha': ''})
        # must be "body" field error
        self.assertFormError(self.response.context['comment_form'], 'body', ['This field must not be empty'])
        self.assertFormError(self.response.context['comment_form'], 'captcha', ['This field must not be empty'])

    def test_get_success_url(self):
        """
        Checking successful redirect URL after comment has been sent successfully
        """
        self.request = self.factory.get(reverse('goods:product_detail',
                                                args=(self.product1.pk, self.product1.slug)))

        self.instance.setup(self.request, **{'product_pk': self.product1.pk, 'product_slug': self.product1.slug})
        url = self.instance.get_success_url()
        self.assertURLEqual(reverse('goods:product_detail', args=(self.product1.pk, self.product1.slug)), url)

    def tearDown(self):
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))

        self.redis.hdel(f'product_id:{self.product1.pk}', 'views')
        self.redis.persist(f'profile_id:{self.profile.pk}')
        self.redis.srem(f'profile_id:{self.profile.pk}', self.product1.pk)
        self.redis.hdel('captcha:AAA111', 'captcha_text')


class TestFilterResultsView(TestCase):
    """
    Testing methods of the class FilterResultsView
    """

    def setUp(self):
        self.random_number = randint(1, 50)
        self.client = Client()
        self.factory = RequestFactory()

        self.category_1 = Category.objects.create(name='Mobile phones', slug='mobile-phones')
        self.category_2 = Category.objects.create(name='Laptops', slug='laptops')

        self.manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                         slug=f'manufacturer_{self.random_number}',
                                                         description='Description')

        self.manufacturer2 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number + 1}',
                                                         slug=f'manufacturer_{self.random_number + 1}',
                                                         description='Description')

        self.manufacturer3 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number + 2}',
                                                         slug=f'manufacturer_{self.random_number + 2}',
                                                         description='Description')

        self.product1 = Product.objects.create(name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=self.manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=self.category_2)

        self.product2 = Product.objects.create(name=f'Product_{self.random_number + 1}',
                                               slug=f'product_{self.random_number + 1}',
                                               manufacturer=self.manufacturer2,
                                               price=Decimal('650.45'),
                                               description='Description',
                                               category=self.category_2)

        self.product3 = Product.objects.create(name=f'Product_{self.random_number + 2}',
                                               slug=f'product_{self.random_number + 2}',
                                               manufacturer=self.manufacturer2,
                                               price=Decimal('100.00'),
                                               description='Description',
                                               category=self.category_1)

        self.product4 = Product.objects.create(name=f'Product_{self.random_number + 3}',
                                               slug=f'product_{self.random_number + 3}',
                                               manufacturer=self.manufacturer3,
                                               price=Decimal('1500.50'),
                                               description='Description',
                                               category=self.category_1)

        self.property_category1 = PropertyCategory.objects.create(name='Display')
        self.property_category2 = PropertyCategory.objects.create(name='Software')
        self.property_category3 = PropertyCategory.objects.create(name='Internal Memory')

        self.property1 = Property.objects.create(name='Volume',
                                                 numeric_value=Decimal('256'),
                                                 units='Gb',
                                                 category_property=self.property_category3,
                                                 product=self.product2)

        self.property2 = Property.objects.create(name='Diagonal',
                                                 numeric_value=Decimal('15.6'),
                                                 units='"',
                                                 category_property=self.property_category1,
                                                 product=self.product3)

        self.property3 = Property.objects.create(name='Volume',
                                                 numeric_value=Decimal('256'),
                                                 units='Gb',
                                                 category_property=self.property_category3,
                                                 product=self.product1)

        self.property4 = Property.objects.create(name='OS',
                                                 text_value='Linux',
                                                 category_property=self.property_category2,
                                                 product=self.product4)

        self.instance = FilterResultsView()

    def test_filtering_products_process_by_passed_parameters(self):
        """
        Checking keys and values in context dict, queryset content, handling the GET method.
        """
        # search product1 and product2
        # make request with min price, max price, manufacturers and properties as data
        response = self.client.get(reverse('goods:filter_results_list', args=(self.category_2.slug, 1)),
                                   data={'price_min': Decimal('100.00'),
                                         'price_max': Decimal('1500.50'),
                                         'manufacturer': [self.manufacturer2.pk, self.manufacturer1.pk],
                                         # props format formed in template
                                         'props': [f'{self.property_category3.pk},Volume,,256']})

        self.request = response.wsgi_request
        # add data to view instance's kwargs
        self.instance.setup(self.request,
                            **{'category_slug': self.category_2.slug,
                               'filter_price': (self.request.GET.get('price_min'), self.request.GET.get('price_max')),
                               'props': self.request.GET.getlist('props'),
                               'filter_manufacturers': self.request.GET.getlist('manufacturer')})

        qs = self.instance.get_queryset()  # in queryset must be product1 and product2, that match the search parameters

        setattr(self.instance, 'filter_qs', qs)  # add attribute, that added as None in __init__ view's method
        setattr(self.instance, 'object_list', [])

        self.assertQuerysetEqual(qs, [self.product1, self.product2], ordered=False)
        context = self.instance.get_context_data()

        # whether the key exists in context
        for key in ('object_list', 'products', 'place', 'category', 'category_properties',
                    'filter_manufacturers', 'manufacturers_prod_qnty', 'sorting_by_price'):
            self.assertIn(key, context)

        # checking context values
        for key, value in context.items():
            if key == 'object_list':
                self.assertEqual(value, [])
            elif key == 'products':
                self.assertEqual(value, [])
            elif key == 'place':
                self.assertEqual(value, 'filter_list')
            elif key == 'category':
                self.assertEqual(value, self.category_2)
            elif key == 'category_properties':
                self.assertEqual(value, {'Internal Memory': [
                    {'translations__name': 'Volume',
                     'translations__text_value': '',
                     'numeric_value': Decimal('256.00'),
                     'translations__units': 'Gb',
                     'category_property': 'Internal Memory',
                     'category_property_pk': self.property_category3.pk,
                     'item_count': 2}]})
            elif key == 'filter_manufacturers':
                self.assertIsInstance(value, FilterByManufacturerForm)
            elif key == 'manufacturers_prod_qnty':
                self.assertEqual(value, {self.manufacturer1.name: 1, self.manufacturer2.name: 1})
            elif key == 'sorting_by_price':
                self.assertIsInstance(value, SortByPriceForm)

        # search product3 and product4
        # make request with min price, max price, manufacturers and properties as data
        response = self.client.get(reverse('goods:filter_results_list', args=(self.category_1.slug, 1)),
                                   data={'price_min': Decimal('100.00'),
                                         'price_max': Decimal('1500.50'),
                                         'manufacturer': [self.manufacturer2.pk, self.manufacturer3.pk],
                                         'props': [
                                             f'{self.property_category2.pk},OS,Linux,0',
                                             f'{self.property_category1.pk},Diagonal,,15.6',
                                         ]})  # props format formed in template

        self.request = response.wsgi_request
        # add data to view instance's kwargs with "filter_price"
        self.instance.setup(self.request,
                            **{'category_slug': self.category_1.slug,
                               'filter_price': (self.request.GET.get('price_min'), self.request.GET.get('price_max')),
                               'props': self.request.GET.getlist('props'),
                               'filter_manufacturers': self.request.GET.getlist('manufacturer')})

        qs = self.instance.get_queryset()  # in queryset must be product3 and product4, that match the search parameters

        setattr(self.instance, 'filter_qs', qs)  # edit attribute, that added as None in __init__ view's method
        setattr(self.instance, 'object_list', [])

        context = self.instance.get_context_data()
        self.assertQuerysetEqual(qs, [self.product3, self.product4], ordered=False)

        # checking context values
        for key, value in context.items():
            if key == 'object_list':
                self.assertEqual(value, [])
            elif key == 'products':
                self.assertEqual(value, [])
            elif key == 'place':
                self.assertEqual(value, 'filter_list')
            elif key == 'category':
                self.assertEqual(value, self.category_1)
            elif key == 'category_properties':
                self.assertEqual(value, {'Display': [
                    {'translations__name': 'Diagonal',
                     'translations__text_value': '',
                     'numeric_value': Decimal('15.60'),
                     'translations__units': '"',
                     'category_property': 'Display',
                     'category_property_pk': self.property_category1.pk,
                     'item_count': 1}],
                    'Software': [
                        {'translations__name': 'OS',
                         'translations__text_value': 'Linux',
                         'numeric_value': Decimal('0.00'),
                         'translations__units': '',
                         'category_property': 'Software',
                         'category_property_pk': self.property_category2.pk,
                         'item_count': 1}]})
            elif key == 'filter_manufacturers':
                self.assertIsInstance(value, FilterByManufacturerForm)
            elif key == 'manufacturers_prod_qnty':
                self.assertEqual(value, {self.manufacturer2.name: 1, self.manufacturer3.name: 1})
            elif key == 'sorting_by_price':
                self.assertIsInstance(value, SortByPriceForm)

        # add data to view instance's kwargs without "filter_price"
        self.instance.setup(self.request,
                            **{'category_slug': self.category_1.slug,
                               'props': self.request.GET.getlist('props'),
                               'filter_manufacturers': self.request.GET.getlist('manufacturer')})

        qs = self.instance.get_queryset()  # in queryset must be product3 and product4, that match the search parameters

        setattr(self.instance, 'filter_qs', qs)  # edit attribute, that added as None in __init__ view's method
        setattr(self.instance, 'object_list', [])

        context = self.instance.get_context_data()
        self.assertQuerysetEqual(qs, [self.product3, self.product4])

        # checking context values
        for key, value in context.items():
            if key == 'object_list':
                self.assertEqual(value, [])
            elif key == 'products':
                self.assertEqual(value, [])
            elif key == 'place':
                self.assertEqual(value, 'filter_list')
            elif key == 'category':
                self.assertEqual(value, self.category_1)
            elif key == 'category_properties':
                self.assertEqual(value, {'Display': [
                    {'translations__name': 'Diagonal',
                     'translations__text_value': '',
                     'numeric_value': Decimal('15.60'),
                     'translations__units': '"',
                     'category_property': 'Display',
                     'category_property_pk': self.property_category1.pk,
                     'item_count': 1}],
                    'Software': [
                        {'translations__name': 'OS',
                         'translations__text_value': 'Linux',
                         'numeric_value': Decimal('0.00'),
                         'translations__units': '',
                         'category_property': 'Software',
                         'category_property_pk': self.property_category2.pk,
                         'item_count': 1}]})
            elif key == 'filter_manufacturers':
                self.assertIsInstance(value, FilterByManufacturerForm)
            elif key == 'manufacturers_prod_qnty':
                self.assertEqual(value, {self.manufacturer2.name: 1, self.manufacturer3.name: 1})
            elif key == 'sorting_by_price':
                self.assertIsInstance(value, SortByPriceForm)

    def tearDown(self):
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product3.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product4.name}'))


class TestOtherGoodsViews(TestCase):
    """
    Testing other views of the goods application
    """

    @property
    def populars(self):
        return self._popular_list

    @populars.setter
    def populars(self, value):
        if isinstance(value, list):
            self._popular_list = value

    @property
    def new(self):
        return self._new_list

    @new.setter
    def new(self, value):
        if isinstance(value, list):
            self._new_list = value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # storage for previous data in redis before the test being start
        self._popular_list = []
        self._new_list = []

    def __iter__(self):
        """
        Iterate through products
        """
        for name, value in self.__dict__.items():
            if name.startswith('product'):
                yield value

    def setUp(self):
        self.random_number = randint(1, 50)
        # default user
        self.user = User.objects.create_user(username='User', password='password')
        self.user.set_password('password')
        self.profile = Profile.objects.create(user=self.user)

        Favorite.objects.create(profile=self.profile)

        category_1 = Category.objects.create(name=f'Category_{self.random_number}',
                                             slug=f'category-{self.random_number}')
        category_2 = Category.objects.create(name=f'category_{self.random_number + 1}',
                                             slug=f'category-{self.random_number + 1}')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                    slug=f'manufacturer_{self.random_number}',
                                                    description='Description')

        manufacturer2 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number + 1}',
                                                    slug=f'manufacturer_{self.random_number + 1}',
                                                    description='Description')

        # ids 1000000, 1000001, 1000002 for interaction with redis, cause not overwrite necessary real values
        self.product1 = Product.objects.create(id=1000000,
                                               name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category_2)
        # promotional product
        self.product2 = Product.objects.create(id=1000001,
                                               name=f'Product_{self.random_number + 1}',
                                               slug=f'product_{self.random_number + 1}',
                                               manufacturer=manufacturer2,
                                               promotional=True,
                                               promotional_price=Decimal('400.45'),
                                               price=Decimal('500.35'),
                                               description='Description',
                                               category=category_2)
        # promotional product
        self.product3 = Product.objects.create(id=1000002,
                                               name=f'Product_{self.random_number + 2}',
                                               slug=f'product_{self.random_number + 2}',
                                               manufacturer=manufacturer2,
                                               promotional=True,
                                               promotional_price=Decimal('120.00'),
                                               price=Decimal('145.50'),
                                               description='Description',
                                               category=category_1)

        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('common.moduls_init.redis', new=redis_instance)
        self.redis = redis_patcher.start()  # mock redis instance

    def test_add_or_remove_product_favorite_for_authenticated_user(self):
        """
        Checking add or remove product into/from profile's favorite, if the profile is authenticated
        """

        self.client.login(username=self.user.username, password='password')
        # add product to favorite
        response = self.client.post(reverse('goods:add_or_remove_product_favorite'),
                                    data={'product_id': self.product1.pk, 'action': 'add'},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest', 'HTTP_REFERER': 'http://testserver/'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_content = json.loads(response.content)
        self.assertIsInstance(response, JsonResponse)
        self.assertIn('amount_prods', response_content)
        self.assertEqual(response_content['amount_prods'], 1)  # must be one product in profile's favorite

        # remove product from favorite
        response = self.client.post(reverse('goods:add_or_remove_product_favorite'),
                                    data={'product_id': self.product1.pk, 'action': 'remove'},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest', 'HTTP_REFERER': 'http://testserver/'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_content = json.loads(response.content)
        self.assertIsInstance(response, JsonResponse)
        self.assertIn('amount_prods', response_content)
        self.assertEqual(response_content['amount_prods'], 0)  # must be nothing in profile's favorite

    def test_add_product_to_favorite_for_unauthenticated_user(self):
        """
        Checking add product into profile's favorite, if the profile isn't authenticated.
        """
        # add product to favorite
        response = self.client.post(reverse('goods:add_or_remove_product_favorite'),
                                    data={'product_id': self.product1.pk, 'action': 'add'},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest',
                                       'HTTP_REFERER': 'http://testserver/en/'})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # must be unauthorized status

        response_content = json.loads(response.content)
        self.assertIsInstance(response, JsonResponse)
        self.assertIn('login_page_url', response_content)
        # redirection link to login page
        redirect_url = f'{reverse("login")}?next={reverse("goods:product_list")}'
        self.assertURLEqual(response_content['login_page_url'], redirect_url)

    def test_promotion_list_view(self):
        """
        Checking displaying products that are promotional
        """
        # request without passing category
        response = self.client.get(reverse('goods:promotion_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertEqual(context['category'], '')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product3], ordered=False)

        # request with passing category
        response = self.client.get(reverse('goods:promotion_list_by_category', args=(self.product2.category.slug,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        context = response.context

        paginator = context['page_obj'].paginator

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        # must be only product2, because it is promotional
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertEqual(context['category'], self.product2.category)
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(paginator.object_list, [self.product2])

    def test_promotion_list_view_if_was_passed_not_existing_page(self):
        """
        Checking displaying products that are promotional if was passed not existing page
        """
        # request without passing category; must be maximum 2 pages, but sent page 3
        response = self.client.get(reverse('goods:promotion_list'), data={'page': 3})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        # must be only one product, since it is on the last page
        self.assertQuerysetEqual(context['products'], [self.product3] or [self.product1] or [self.product2])
        self.assertEqual(context['category'], '')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product3])

        # request with passing category
        response = self.client.get(reverse('goods:promotion_list_by_category', args=(self.product2.category.slug,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        context = response.context

        paginator = context['page_obj'].paginator

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        # must be only product2, because it is promotional
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertEqual(context['category'], self.product2.category)
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(paginator.object_list, [self.product2])

    def test_new_list_view(self):
        """
        Checking displaying products that are new on the site
        """
        # make product as not new on the site
        # created date must be greater than or equal 2 weeks
        product_created_data = self.product3.created
        self.product3.created = product_created_data - timezone.timedelta(weeks=3)
        self.product3.save()

        # request without passing category
        response = self.client.get(reverse('goods:new_list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertEqual(context['category'], '')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        # must be 2 products inside object_list, because product3 is not new (added greater than 2 weeks ago)
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2], ordered=False)

        redis_new_prods_ids = self.redis.hget('new_prods', 'ids')  # check records in redis DB
        self.assertEqual(redis_new_prods_ids, f'{self.product1.pk},{self.product2.pk}')

        # request with passing category
        response = self.client.get(reverse('goods:new_list_by_category', args=(self.product3.category.slug,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product3.category)
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        # must not be any products, because received category contains only product3 which considered as not new
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertQuerysetEqual(paginator.object_list, [])

    def test_popular_list_view(self):
        """
        Checking displaying products that are popular on the site
        """
        # add id of each product to redis
        for product in self:
            self.redis.sadd('products_ids', product.pk)

        # add views for each product to redis -> 5, 10, 15 views
        for product, views in zip(self, (v for v in (5, 10, 15))):
            self.redis.hset(f'product_id:{product.pk}', 'views', views)

        try:
            self.populars = self.redis.hget('popular_prods', 'ids').split(',')  # might be empty
        except AttributeError:
            pass

        # set products as populars, adding products ids to redis to "popular_prods" hash name
        self.redis.hset('popular_prods', 'ids', ','.join(str(product.pk) for product in self))

        # request without passing category
        response = self.client.get(reverse('goods:popular_list'))
        context = response.context

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        # product3 has 15 views, product2 has 10 views
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertQuerysetEqual(paginator.object_list, [self.product3, self.product2, self.product1])

        # request with passing category
        response = self.client.get(reverse('goods:popular_list_by_category', args=(self.product1.category.slug,)))
        context = response.context

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')
        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price', 'is_paginated', 'is_sorting', 'place'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertFalse(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        # product3 has 15 views, product2 has 10 views
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1])  # must be 2 products

    def test_product_ordering_in_main_list_without_category(self):
        """
        Checking ordering products by ascending or descending price in main list of the products without category
        """
        # add id of each product to redis
        for product in self:
            self.redis.sadd('products_ids', product.pk)

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'mainlist', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'mainlist')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(300.25), product2(400.45), product3(120.00)
        self.assertQuerysetEqual(paginator.object_list, [self.product3, self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'mainlist', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'mainlist')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(300.25), product3(120.00)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1, self.product3])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'mainlist', 'category_slug': 'all', 'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'mainlist')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # may be whichever order of the products
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2, self.product3], ordered=False)

    def test_product_ordering_in_main_list_with_category(self):
        """
        Checking ordering products by ascending or descending price in main list of the products with category
        """
        # add id of each product to redis
        for product in self:
            self.redis.sadd('products_ids', product.pk)

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'mainlist',
                                                   'category_slug': self.product1.category.slug,  # add category
                                                   'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'mainlist')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(300.25), product2(400.45)
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'mainlist',
                                                   'category_slug': self.product1.category.slug,  # add category
                                                   'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'mainlist')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(300.25)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'mainlist',
                                                   'category_slug': self.product1.category.slug,  # add category
                                                   'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'mainlist')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # may be whichever order of the products
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2], ordered=False)

    def test_product_ordering_in_popular_list_without_category(self):
        """
        Checking ordering products by ascending or descending price in popular list of the products without category
        """

        # add id of each product to redis
        for product in self:
            self.redis.sadd('products_ids', product.pk)

        # add views for each product to redis -> 10, 5, 15 views
        for product, views in zip(self, (v for v in (10, 5, 15))):
            self.redis.hset(f'product_id:{product.pk}', 'views', views)

        # save to property existing records in redis from "popular_prods" hash name
        try:
            self.populars = self.redis.hget('popular_prods', 'ids').split(',')  # might be empty
        except AttributeError:
            pass

        # set products as populars, adding products ids to redis to "popular_prods" hash name
        self.redis.hset('popular_prods', 'ids', ','.join(str(product.pk) for product in self))

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'popular', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product3(120.00) product1(300.25), product2(400.45),
        self.assertQuerysetEqual(paginator.object_list, [self.product3, self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'popular', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(300.25), product3(120.00)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1, self.product3])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'popular', 'category_slug': 'all', 'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertTrue(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # the order of products can be whichever
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2, self.product3], ordered=False)

    def test_product_ordering_in_new_list_without_category(self):
        """
        Checking ordering products by ascending or descending price in new list of the products without category
        """
        # make product as not new on the site
        # created date must be greater than or equal 2 weeks
        product_created_data = self.product3.created
        self.product3.created = product_created_data - timezone.timedelta(weeks=3)
        self.product3.save()

        # save to property existing records in redis from "new_prods" hash name
        try:
            self.new = self.redis.hget('new_prods', 'ids').split(',')  # might be empty
        except AttributeError:
            pass

        # set products as populars, adding products ids to redis to "new_prods" hash name
        # product3 considered as not new
        self.redis.hset('new_prods', 'ids', ','.join(str(product.pk) for product in (self.product1, self.product2)))

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'new', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(300.25), product2(400.45),
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'new', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(300.25)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'new', 'category_slug': 'all', 'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # the order of products can be whichever
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2], ordered=False)

    def test_product_ordering_in_promotional_list_without_category(self):
        """
        Checking ordering products by ascending or descending price in promotional list of the products without category
        """

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'promotion', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product3(120.00), product2(400.45),
        self.assertQuerysetEqual(paginator.object_list, [self.product3, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'promotion', 'category_slug': 'all', 'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product3(120.00)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product3])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'promotion', 'category_slug': 'all', 'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertIsNone(context['category'])
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # the order of products can be whichever
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product3], ordered=False)

    def test_product_ordering_in_popular_list_with_category(self):
        """
        Checking ordering products by ascending or descending price in popular list of the products with category
        """

        # add id of each product to redis
        for product in self:
            self.redis.sadd('products_ids', product.pk)

        # add views for each product to redis -> 10, 5, 15 views
        for product, views in zip(self, (v for v in (10, 5, 15))):
            self.redis.hset(f'product_id:{product.pk}', 'views', views)

        # save to property existing records in redis from "popular_prods" hash name
        try:
            self.populars = self.redis.hget('popular_prods', 'ids').split(',')  # might be empty
        except AttributeError:
            pass

        # set products as populars, adding products ids to redis to "popular_prods" hash name
        self.redis.hset('popular_prods', 'ids', ','.join(str(product.pk) for product in self))

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'popular',
                                                   'category_slug': self.product1.category.slug,
                                                   'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(300.25), product2(400.45),
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'popular',
                                                   'category_slug': self.product1.category.slug,
                                                   'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(300.25)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'popular',
                                                   'category_slug': self.product1.category.slug,
                                                   'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'popular')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # the order of products can be whichever
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2], ordered=False)

    def test_product_ordering_in_new_list_with_category(self):
        """
        Checking ordering products by ascending or descending price in new list of the products with category
        """
        # make product as not new on the site
        # created date must be greater than or equal 2 weeks
        # change category of product3; all products belongs to category2 now
        product_created_data = self.product3.created
        self.product3.created = product_created_data - timezone.timedelta(weeks=3)
        self.product3.category = self.product1.category
        self.product3.save()

        # save to property existing records in redis from "new_prods" hash name
        try:
            self.new = self.redis.hget('new_prods', 'ids').split(',')  # might be empty
        except AttributeError:
            pass

        # set products as populars, adding products ids to redis to "new_prods" hash name
        # product3 considered as not new
        self.redis.hset('new_prods', 'ids', ','.join(str(product.pk) for product in (self.product1, self.product2)))

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'new',
                                                   'category_slug': self.product3.category.slug,
                                                   'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product3.category)
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(300.25), product2(400.45),
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'new',
                                                   'category_slug': self.product3.category.slug,
                                                   'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product3.category)
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(300.25)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'new',
                                                   'category_slug': self.product3.category.slug,
                                                   'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product3.category)
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'new')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # the order of products can be whichever
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2], ordered=False)

    def test_product_ordering_in_promotional_list_with_category(self):
        """
        Checking ordering products by ascending or descending price in promotional list of the products with category
        """
        # make product1 as promotional
        self.product1.promotional = True
        self.product1.promotional_price = Decimal('295.00')
        self.product1.save()

        # sorting products ascending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'promotion',
                                                   'category_slug': self.product1.category.slug,
                                                   'page': 1}),
                                   data={'sort': 'p_asc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertEqual(context['selected_sort'], 'p_asc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(295.00), product2(400.45),
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2])

        # sorting products descending
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'promotion',
                                                   'category_slug': self.product1.category.slug,
                                                   'page': 1}),
                                   data={'sort': 'p_desc'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertEqual(context['selected_sort'], 'p_desc')
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product2(400.45) product1(295.00)
        self.assertQuerysetEqual(paginator.object_list, [self.product2, self.product1])

        # sorting products by default
        response = self.client.get(reverse('goods:product_ordering',
                                           kwargs={'place': 'promotion',
                                                   'category_slug': self.product1.category.slug,
                                                   'page': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'goods/product/navs_categories_list.html')

        context = response.context

        # expected keys in the context
        for key in ('products', 'page_obj', 'category', 'sorting_by_price',
                    'is_paginated', 'is_sorting', 'place', 'selected_sort'):
            self.assertIn(key, context)

        paginator = context['page_obj'].paginator

        self.assertEqual(context['category'], self.product1.category)
        self.assertIsNone(context['selected_sort'])
        self.assertIsInstance(context['sorting_by_price'], SortByPriceForm)
        self.assertFalse(context['is_paginated'])  # depending on page_obj.paginator.object_list length
        self.assertTrue(context['is_sorting'])
        self.assertEqual(context['place'], 'promotion')
        self.assertQuerysetEqual(context['products'],
                                 # result depends on "per_page" value
                                 [p for n, p in enumerate(paginator.object_list, 1) if n <= paginator.per_page])
        # must be product1(295.00), product2(400.45)
        self.assertQuerysetEqual(paginator.object_list, [self.product1, self.product2])

    def test_set_product_rating(self):
        """
        Checking how setting product rating
        """
        response = self.client.post(reverse('goods:set_product_rating'),
                                    data={'product_id': self.product1.pk, 'star': 3},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response, JsonResponse)
        response_content = json.loads(response.content)
        self.assertIn('current_rating', response_content)
        self.assertEqual(response_content['current_rating'], '3.0')

        response = self.client.post(reverse('goods:set_product_rating'),
                                    data={'product_id': self.product1.pk, 'star': 5},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        response_content = json.loads(response.content)
        self.assertEqual(response_content['current_rating'], '4.0')

        response = self.client.post(reverse('goods:set_product_rating'),
                                    data={'product_id': self.product1.pk, 'star': 2},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        response_content = json.loads(response.content)
        self.assertEqual(response_content['current_rating'], '3.0')

    def tearDown(self) -> None:
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product3.name}'))
        self.redis.hdel('new_prods', 'ids')
        # delete product id and views from redis
        for product in self:
            self.redis.srem('products_ids', product.pk)
            self.redis.hdel(f'product_id:{product.pk}', 'views')

        if self.populars:
            # restore previous popular products ids
            self.redis.hset('popular_prods', 'ids', ','.join(self.populars))
            self.populars.clear()

        if self.new:
            # restore previous new products ids
            self.redis.hset('new_prods', 'ids', ','.join(self.new))
            self.new.clear()
