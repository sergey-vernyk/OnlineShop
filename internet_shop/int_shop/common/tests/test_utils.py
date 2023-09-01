import json
from random import randint
from unittest.mock import patch

import redis as strict_redis
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.http.response import JsonResponse
from django.shortcuts import reverse
from django.test import TestCase, RequestFactory
from django.utils import timezone

from common.utils import (
    ValidDiscountsListFilter,
    create_random_text_for_captcha,
    create_captcha_image,
    validate_captcha_text
)
from common.utils import check_phone_number
from coupons.admin import CouponAdmin
from coupons.models import Coupon, Category as Coupon_Category
from present_cards.admin import PresentCardAdmin
from present_cards.models import PresentCard, Category as PresentCard_Category


class TestCommonUtils(TestCase):
    """
    Testing utils for site
    """

    def setUp(self) -> None:
        redis_instance = strict_redis.StrictRedis(host=settings.REDIS_HOST,
                                                  port=settings.REDIS_PORT,
                                                  db=settings.REDIS_DB_NUM,
                                                  charset='utf-8',
                                                  socket_timeout=30)

        redis_patcher = patch('common.utils.redis', redis_instance)
        self.redis = redis_patcher.start()

        self.random_text_captcha = 'ABC123'

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

    def test_check_phone_number_if_number_is_not_correct(self):
        """
        Checking whether passed phone number is not correct
        """
        wrong_phone_number_one_extra_digit = '+3809912345678'
        result = check_phone_number(wrong_phone_number_one_extra_digit)
        self.assertFalse(result)

        wrong_phone_number_one_missing_digit = '+38099123456'
        result = check_phone_number(wrong_phone_number_one_missing_digit)
        self.assertFalse(result)

        wrong_phone_number_without_country_code = '09912345678'
        result = check_phone_number(wrong_phone_number_without_country_code)
        self.assertFalse(result)

        wrong_phone_number_not_ukrainian_number = '+380881234567'
        result = check_phone_number(wrong_phone_number_not_ukrainian_number)
        self.assertFalse(result)

    def test_check_phone_number_if_number_is_correct(self):
        """
        Checking whether passed phone number is correct
        """
        phone_number_vodafone = '+38{}1234567'
        for code in ('099', '095', '050'):
            result = check_phone_number(phone_number_vodafone.format(code))
            self.assertEqual(result, phone_number_vodafone.format(code))

        phone_number_lifecell = '+38{}1234567'
        for code in ('063', '093', '073'):
            result = check_phone_number(phone_number_lifecell.format(code))
            self.assertEqual(result, phone_number_lifecell.format(code))

        phone_number_kyivstar = '+38{}1234567'
        for code in ('067', '097', '098'):
            result = check_phone_number(phone_number_kyivstar.format(code))
            self.assertEqual(result, phone_number_kyivstar.format(code))

    @patch('common.utils.choices')
    def test_create_random_text_for_captcha(self, mock_random):
        """
        Checking creating random captcha text
        """
        mock_random.return_value = ['1', 'C', 'A', 'K', '8', 'U']
        result = create_random_text_for_captcha(6)
        self.assertEqual(result, '1CAK8U')

    def test_create_captcha_image(self):
        """
        Checking creating captcha from text
        """
        factory = RequestFactory()

        request_get = factory.get(reverse('update_captcha'))
        response = create_captcha_image(request_get)
        self.assertIsInstance(response, str)  # must only str, if request is GET

        # request POST needs AJAX header
        request_post = factory.post(reverse('update_captcha'),
                                    data={'width': 200, 'height': 60, 'font_size': 30},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        response = create_captcha_image(request_post)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)  # must be JsonResponse with captcha image value
        response_content = json.loads(response.content)
        self.assertIn('captcha_image', response_content)
        self.assertIsInstance(response_content['captcha_image'], str)

    def test_validate_captcha_text(self):
        """
        Checking whether captcha text is valid or not
        """
        self.redis.hset(f'captcha:{self.random_text_captcha}', 'captcha_text', self.random_text_captcha)
        # captcha is correct
        cleaned_data = {'captcha': self.random_text_captcha}
        result = validate_captcha_text(cleaned_data)
        self.assertEqual(result, self.random_text_captcha)

        # captcha was not provided
        cleaned_data = {'captcha': ''}
        self.assertRaises(ValidationError, validate_captcha_text, **{'cleaned_data': cleaned_data})

        # captcha was wrong
        cleaned_data = {'captcha': '123HGK'}
        self.assertRaises(ValidationError, validate_captcha_text, **{'cleaned_data': cleaned_data})

    def tearDown(self) -> None:
        self.redis.hdel(f'captcha:{self.random_text_captcha}', 'captcha_text')
