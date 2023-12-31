import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.auth.models import User
from django.http import QueryDict
from django.shortcuts import reverse
from django.template import Template, Context
from django.test import TestCase, Client, RequestFactory

from account.models import Profile
from goods.models import (
    Product,
    Category,
    Manufacturer,
    PropertyCategory,
    Property,
    Favorite
)
from goods.views import ProductListView


class TestTemplatetagsGoods(TestCase):
    """
    Testing templatetags in goods application
    """

    def setUp(self) -> None:
        self.random_number = randint(1, 50)

        self.category_1 = Category.objects.create(name='Smart Gadgets',
                                                  slug='smart-gadgets')
        self.manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{self.random_number}',
                                                         slug=f'manufacturer_{self.random_number}',
                                                         description='Description')

        self.product1 = Product.objects.create(name=f'Product_{self.random_number}',
                                               slug=f'product_{self.random_number}',
                                               manufacturer=self.manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=self.category_1)

        self.product2 = Product.objects.create(name=f'Product_{self.random_number + 1}',
                                               slug=f'product_{self.random_number + 1}',
                                               manufacturer=self.manufacturer1,
                                               price=Decimal('100.00'),
                                               description='Description',
                                               category=self.category_1)

        self.product3 = Product.objects.create(name=f'Product_{self.random_number + 2}',
                                               slug=f'product_{self.random_number + 2}',
                                               manufacturer=self.manufacturer1,
                                               price=Decimal('650.80'),
                                               description='Description',
                                               category=self.category_1)

        self.property_category1 = PropertyCategory.objects.create(name='Internal Memory')
        self.property1 = Property.objects.create(name='Volume',
                                                 numeric_value=Decimal('256'),
                                                 units='Gb',
                                                 category_property=self.property_category1,
                                                 product=self.product1)

        self.user = User.objects.create_user(username='testuser', password='password')
        self.user.set_password('password')
        self.profile = Profile.objects.create(user=self.user)
        Favorite.objects.create(profile=self.profile)

    def test_check_request_tag_return_true(self):
        """
        Checking simple tag, which should return true about contains certain data in GET request dict
        """
        query_dict = QueryDict(
            f'props={self.property_category1.pk},{self.property1.name},,{self.property1.numeric_value}'
        )
        props = query_dict.get('props')
        # data in context and query_dict does match entirely
        context = Context(
            {'data': {k: v for k, v in zip(('category_property_pk', 'name', 'text_value', 'numeric_value'),
                                           props.split(','))},
             'request_get': query_dict
             })

        template = Template('{% load check_data_in_request %}'
                            '{% check_request request_get'
                            ' data.category_property_pk'
                            ' data.name'
                            ' data.text_value'
                            ' data.numeric_value %}')
        result = template.render(context)
        self.assertTrue(result == 'True')  # result is the instance of SafeString, not bool

    def test_check_request_tag_return_false(self):
        """
        Checking simple tag, which should returns false about contains certain data in GET request dict
        """
        query_dict = QueryDict(
            f'props={self.property_category1.pk},{self.property1.name},,{self.property1.numeric_value}'
        )
        # data in context and query_dict doesn't match entirely
        context = Context(
            {'data': {k: v for k, v in zip(('category_property_pk', 'name', 'text_value', 'numeric_value'),
                                           [str(self.property_category1.pk), {self.property1.name}, '', '128'])},
             'request_get': query_dict
             })

        template = Template('{% load check_data_in_request %}'
                            '{% check_request request_get'
                            ' data.category_property_pk'
                            ' data.name'
                            ' data.text_value'
                            ' data.numeric_value %}')
        result = template.render(context)
        self.assertTrue(result == 'False')  # result is the instance of SafeString, not bool

    def test_cut_fraction_filter(self):
        """
        Checking custom filter, which checks data after decimal point in passed number
        """
        context = Context({'data': {
            'number1': Decimal('15.60'),
            'number2': Decimal('10.00')
        }})

        template = Template('{% load cut_fraction_part %}'
                            'number1: {{ data.number1|cut_fraction }}, '
                            'number2: {{ data.number2|cut_fraction }}')
        result = template.render(context)
        self.assertEqual(result, 'number1: 15.60, number2: 10')

    def test_split_filter(self):
        """
        Checking custom filter, which split full path to the resource into the URL for the filter,
        and the URL with the filter request.
        """
        client = Client()
        response = client.get(reverse('goods:filter_results_list', args=(self.category_1.slug, 1)),
                              data={'price_min': Decimal('100.00'),
                                    'price_max': Decimal('1500.50')}, **{'HTTP_ACCEPT_LANGUAGE': 'en'})

        request = response.wsgi_request

        context = Context({
            'data': {
                'request': request
            }
        })

        template = Template('{% load split_full_path %}'
                            '{{ data.request|split:1|safe }}')  # safe filter for displaying "&" instead of "&amp;"
        self.assertEqual(template.render(context), '?price_min=100.00&price_max=1500.50')

        template = Template('{% load split_full_path %}'
                            '{{ data.request|split:0 }}')
        # simulate filter result by cutting `/1/` from the end of the path
        self.assertEqual(template.render(context), context['data']['request'].path.replace('/1/', ''))

    def test_get_elided_page_range_paginator(self):
        """
        Checking custom tag, which has to return list of page numbers,
        and in this list may be ellipsis
        """
        factory = RequestFactory()
        request = factory.get(reverse('goods:product_list'))
        request.user = self.user

        instance = ProductListView()
        setattr(instance, 'object_list', [self.product1, self.product2, self.product3])
        setattr(instance, 'profile', self.profile)
        setattr(instance, 'paginate_by', 1)  # override paginate_by class attribute
        instance.setup(request)

        context = instance.get_context_data()

        context = Context({
            'data': {
                'paginator': context['paginator'],
                'number': context['page_obj'].number,
                'on_each_side': 1,
                'on_ends': 1,
            }})

        template = Template('{% load get_elided_page_range_paginator %}'
                            '{% get_elided_page_range_paginator data.paginator data.number'
                            ' data.on_each_side data.on_ends as elided_page_range %}'
                            '{% for p in elided_page_range %}?page={{ p }}{% endfor %}')

        self.assertEqual(template.render(context), '?page=1?page=2?page=3')

    def tearDown(self) -> None:
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product3.name}'))
