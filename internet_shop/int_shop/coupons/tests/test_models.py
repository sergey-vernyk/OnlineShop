from random import randint

from django.test import TestCase
from django.utils import timezone

from coupons.models import Coupon, Category


class TestCouponModels(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)
        category_coupon = Category.objects.create(name='For men', slug='for-men')
        cls.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                           valid_from=timezone.now(),
                                           valid_to=timezone.now() + timezone.timedelta(days=10),
                                           discount=20,
                                           category=category_coupon)

    def test_coupons_is_valid_property_if_coupon_really_valid(self):
        """
        Checking whether coupon is valid
        """
        self.coupon.valid_to = timezone.now() + timezone.timedelta(days=10)
        self.coupon.save()
        self.assertTrue(self.coupon.is_valid)

    def test_coupons_is_valid_property_if_coupon_invalid(self):
        """
        Checking whether coupon is invalid
        """
        self.coupon.valid_to = timezone.now() - timezone.timedelta(days=5)
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
