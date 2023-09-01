import json
import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpRequest
from django.http.response import JsonResponse
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory, Client
from django.views.generic import DetailView
from rest_framework import status

from common.decorators import ajax_required, auth_profile_required
from goods.models import Product, Category, Manufacturer


class TestDecorators(TestCase):
    """
    Testing decorators
    """

    def setUp(self) -> None:
        self.random_number = randint(1, 50)
        self.client = Client()

    def test_ajax_required_decorator(self):
        """
        Checking the decorator, that checks request type.
        If request type is AJAX, will return decorated function, otherwise return 400 error
        """
        self.request = HttpRequest()
        self.request.META.update({'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})  # request will be AJAX

        @ajax_required
        def decorated_func(request):
            return HttpResponse('Some response content')

        result = decorated_func(self.request)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.content.decode('utf-8'), 'Some response content')

        self.request = HttpRequest()  # new request without AJAX header

        result = decorated_func(self.request)
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_auth_profile_required_decorator(self):
        """
        Checking the decorator, that checks whether user is authenticated before some action.
        If user is not authenticated,  will return JSON response with error 401,
        otherwise will return decorated function
        """
        self.factory = RequestFactory()

        product_category = Category.objects.create(name=f'product_category_{self.random_number}',
                                                   slug=f'product-category-{self.random_number}')

        manufacturer = Manufacturer.objects.create(name=f'manuf_{self.random_number}',
                                                   slug=f'manuf-{self.random_number}',
                                                   description='Description')

        self.product = Product.objects.create(name=f'product_{self.random_number}',
                                              slug=f'product-{self.random_number}',
                                              manufacturer=manufacturer,
                                              price=Decimal('120.00'),
                                              category=product_category)

        self.request = self.factory.get(reverse('goods:product_detail', args=(self.product.pk, self.product.slug)))
        self.request.session = self.client.session

        user = User.objects.create_user(username='test_user', password='password')
        user.set_password('password')
        self.request.user = user
        self.request.META.update({'HTTP_REFERER': self.request.build_absolute_uri()})  # add referer to headers
        logout(self.request)  # necessary to logout, since user is authenticated by default

        # test when view type is the function and user is not authenticated
        @auth_profile_required
        def decorated_view(request):
            return HttpResponse('Some response content from function view')

        response = decorated_view(self.request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsInstance(response, JsonResponse)
        response_content = json.loads(response.content)
        self.assertIn('login_page_url', response_content)
        # must be redirection to login page and will go to the same page after login
        self.assertEqual(response_content['login_page_url'],
                         (f'{reverse("login")}?next='
                          f'{reverse("goods:product_detail", args=(self.product.pk, self.product.slug))}'))

        # test when view type is the function and user is authenticated
        user = authenticate(self.request, username=user.username, password='password')
        login(self.request, user=user)

        response = decorated_view(self.request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # must return result of the decorated view function
        self.assertEqual(response.content.decode('utf-8'), 'Some response content from function view')

        # test when view type is the CBV and user is not authenticated
        logout(self.request)
        cbv_view = DetailView(model=Product, slug_url_kwarg='product_slug', pk_url_kwarg='product_pk')
        cbv_view.setup(self.request, **{'product_slug': self.product.slug, 'product_pk': self.product.pk})
        setattr(cbv_view, 'object', self.product)

        response = auth_profile_required(cbv_view.get)(self.request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # test when view type is the CBV and user is authenticated
        user = authenticate(self.request, username=user.username, password='password')
        login(self.request, user=user)

        cbv_view = DetailView(model=Product, slug_url_kwarg='product_slug', pk_url_kwarg='product_pk')
        cbv_view.setup(self.request, **{'product_slug': self.product.slug, 'product_pk': self.product.pk})
        setattr(cbv_view, 'object', self.product)

        response = auth_profile_required(cbv_view.get)(self.request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.product, response.context_data['object'])
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product.name}'))
