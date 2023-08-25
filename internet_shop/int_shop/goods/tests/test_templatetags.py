import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.http import QueryDict
from django.shortcuts import reverse
from django.template import Template, Context
from django.test import TestCase, Client

from goods.models import Product, Category, Manufacturer, PropertyCategory, Property


class TestTemplatetagsGoods(TestCase):
    """
    Testing templatetags in goods application
    """

    def setUp(self) -> None:
        random_number = randint(1, 50)

        self.category_1 = Category.objects.create(name='Smart Gadgets',
                                                  slug='smart-gadgets')
        self.manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                         slug=f'manufacturer_{random_number}',
                                                         description='Description')

        self.product1 = Product.objects.create(name=f'Product_{random_number}',
                                               slug=f'product_{random_number}',
                                               manufacturer=self.manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=self.category_1)

        self.property_category1 = PropertyCategory.objects.create(name='Internal Memory')
        self.property1 = Property.objects.create(name='Volume',
                                                 numeric_value=Decimal('256'),
                                                 units='Gb',
                                                 category_property=self.property_category1,
                                                 product=self.product1)

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
                                    'price_max': Decimal('1500.50')})

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

        self.assertEqual(template.render(context), '/goods/smart-gadgets/filter')

    def tearDown(self) -> None:
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
