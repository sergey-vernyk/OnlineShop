from django.test import TestCase, RequestFactory

from coupons.forms import CouponApplyForm
from coupons.models import Coupon, Category
from django.utils import timezone
from django.shortcuts import reverse
from random import randint
import json


class TestCouponForms(TestCase):
    """
    Testing forms in coupons application
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

        cls.factory = RequestFactory()

    def test_receiving_error_when_coupon_invalid(self):
        """
        Checking appear error, when coupon is invalid
        """
        self.coupon.valid_to = timezone.now() - timezone.timedelta(days=5)  # make coupon invalid
        self.coupon.save()

        request = self.factory.post(reverse('coupons:apply_coupon'), {'code': self.coupon.code})

        self.instance = CouponApplyForm(data=request.POST)
        self.instance.is_valid()

        self.assertTrue(self.instance.has_error('code'))  # must be an error
        error_info = self.instance.errors.as_json()
        self.assertEqual(json.loads(error_info)['code'][0]['message'], 'Invalid coupon code')  # error message

    def test_receiving_coupon_code_when_it_valid(self):
        """
        Checking returning coupon code, when coupon is valid.
        There are no errors have to be
        """
        self.coupon.valid_to = timezone.now() + timezone.timedelta(days=10)  # make coupon valid
        self.coupon.save()

        request = self.factory.post(reverse('coupons:apply_coupon'), {'code': self.coupon.code})

        self.instance = CouponApplyForm(data=request.POST)
        self.instance.is_valid()

        self.assertFalse(self.instance.has_error('code'))
