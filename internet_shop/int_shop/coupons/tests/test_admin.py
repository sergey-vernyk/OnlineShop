from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from random import randint
from coupons.models import Coupon, Category
from django.utils import timezone
from coupons.admin import CouponAdmin


class TestAdminCoupons(TestCase):
    """
    Testing methods in admin site
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)
        category_coupon = Category.objects.create(name=f'coupon_category_{random_number + 2}',
                                                  slug=f'coupon-category-{random_number + 2}')

        cls.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                           valid_from=timezone.now(),
                                           valid_to=timezone.now() + timezone.timedelta(days=10),
                                           discount=20,
                                           category=category_coupon)

        cls.site = AdminSite()

    def test_correct_displaying_coupon_validity(self):
        """
        Checking displaying validity coupon in coupons list
        """
        self.instance = CouponAdmin(model=Coupon, admin_site=self.site)
        self.assertEqual(self.instance.is_valid(self.coupon), 'Valid')

        self.coupon.valid_to = timezone.now() - timezone.timedelta(days=5)  # make coupon as invalid
        self.coupon.save()

        self.assertEqual(self.instance.is_valid(self.coupon), 'Invalid')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
