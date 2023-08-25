from random import randint

from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory
from django.utils import timezone

from common.utils import ValidDiscountsListFilter
from coupons.admin import CouponAdmin
from coupons.models import Coupon, Category as Coupon_Category
from present_cards.admin import PresentCardAdmin
from present_cards.models import PresentCard, Category as PresentCard_Category


class TestCommonUtils(TestCase):
    """
    Testing utils for site
    """

    def test_valid_coupons_filter_for_admin_site(self):
        """
        Checking filter by validity coupon
        """
        random_number = randint(1, 50)
        category_coupon = Coupon_Category.objects.create(name=f'coupon_category_{random_number}',
                                                         slug=f'coupon-category-{random_number}')
        # valid coupon
        self.coupon1 = Coupon.objects.create(code=f'coupon_code_{random_number}',
                                             valid_from=timezone.now(),
                                             valid_to=timezone.now() + timezone.timedelta(days=10),
                                             discount=20,
                                             category=category_coupon)
        # invalid coupon
        self.coupon2 = Coupon.objects.create(code=f'coupon_code_{random_number + 1}',
                                             valid_from=timezone.now(),
                                             valid_to=timezone.now() + timezone.timedelta(days=-10),
                                             discount=15,
                                             category=category_coupon)

        self.request = RequestFactory()
        self.site = AdminSite()
        self.instance = ValidDiscountsListFilter(request=self.request,
                                                 model=Coupon,
                                                 model_admin=CouponAdmin,
                                                 params={'validation_status': 'valid'})

        qs = Coupon.objects.filter(id__in=[self.coupon1.pk, self.coupon2.pk])
        result = self.instance.queryset(self.request, qs)
        self.assertQuerysetEqual(result, [self.coupon1])  # must be only valid coupon coupon1

        self.instance = ValidDiscountsListFilter(request=self.request,
                                                 model=Coupon,
                                                 model_admin=CouponAdmin,
                                                 params={'validation_status': 'invalid'})

        qs = Coupon.objects.filter(id__in=[self.coupon1.pk, self.coupon2.pk])
        result = self.instance.queryset(self.request, qs)
        self.assertQuerysetEqual(result, [self.coupon2])  # must be only invalid coupon coupon2

    def test_valid_present_cards_filter_for_admin_site(self):
        """
        Checking filter by validity present card
        """
        random_number = randint(1, 50)
        category_present_card = PresentCard_Category.objects.create(name=f'card_category_{random_number}',
                                                                    slug=f'card-category-{random_number}')
        # valid present card
        self.present_card1 = PresentCard.objects.create(code=f'card_code_{random_number}',
                                                        valid_from=timezone.now(),
                                                        valid_to=timezone.now() + timezone.timedelta(days=10),
                                                        amount=200,
                                                        category=category_present_card)
        # invalid present card
        self.present_card2 = PresentCard.objects.create(code=f'card_code_{random_number + 1}',
                                                        valid_from=timezone.now(),
                                                        valid_to=timezone.now() + timezone.timedelta(days=-10),
                                                        amount=150,
                                                        category=category_present_card)

        self.request = RequestFactory()
        self.site = AdminSite()
        self.instance = ValidDiscountsListFilter(request=self.request,
                                                 model=Coupon,
                                                 model_admin=PresentCardAdmin,
                                                 params={'validation_status': 'valid'})

        qs = PresentCard.objects.filter(id__in=[self.present_card1.pk, self.present_card2.pk])
        result = self.instance.queryset(self.request, qs)
        self.assertQuerysetEqual(result, [self.present_card1])  # must be only valid card present_card1

        self.instance = ValidDiscountsListFilter(request=self.request,
                                                 model=PresentCard,
                                                 model_admin=PresentCardAdmin,
                                                 params={'validation_status': 'invalid'})

        qs = PresentCard.objects.filter(id__in=[self.present_card1.pk, self.present_card2.pk])
        result = self.instance.queryset(self.request, qs)
        self.assertQuerysetEqual(result, [self.present_card2])  # must be only invalid card present_card2
