import os
import shutil
from decimal import Decimal
from random import randint

from django.conf import settings
from django.contrib.admin import AdminSite
from django.test import TestCase

from goods.admin import ProductSummernoteAdmin
from goods.models import Product, Category, Manufacturer, get_product_image_path


class TestAdminGoods(TestCase):
    """
    Testing methods in admin panel
    """

    def setUp(self) -> None:
        random_number = randint(1, 50)
        manufacturer = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                   slug=f'manufacturer-{random_number}')

        category = Category.objects.create(name=f'Some_category_{random_number}',
                                           slug=f'some-category-{random_number}')

        self.product = Product.objects.create(name=f'product_{random_number}',
                                              slug=f'product-{random_number}',
                                              manufacturer_id=manufacturer.pk,
                                              description='Description',
                                              price=Decimal('120.50'),
                                              category_id=category.pk)

        # save path product's image and assign this path as image field attribute
        path = get_product_image_path(self.product, 'product_image.jpg')
        self.product.image = path

        self.site = AdminSite()

    def test_get_image_tag(self):
        """
        Checking correct making product's photo link in change product information menu
        """
        instance = ProductSummernoteAdmin(model=Product, admin_site=self.site)
        link = f'<img src="{self.product.image.url}" width="100" height="100"/>'
        self.assertEqual(instance.get_image_tag(self.product), link)

    def tearDown(self) -> None:
        # deleting product directory from media root
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product.name}'))
