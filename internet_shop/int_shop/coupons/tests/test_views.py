import json
from random import randint

from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.shortcuts import reverse
from django.test import TestCase, Client
from django.utils import timezone

from account.models import Profile
from coupons.models import Coupon, Category


class TestCouponViews(TestCase):
    """
    Testing coupon views
    """

    user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        random_number = randint(1, 50)
        cls.user = User.objects.create_user(username='testuser', password='password')
        cls.user.set_password('password')
        cls.profile = Profile.objects.create(user=cls.user)
        category_coupon = Category.objects.create(name=f'coupon_category_{random_number + 2}',
                                                  slug=f'coupon-category-{random_number + 2}')

        cls.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                           valid_from=timezone.now(),
                                           valid_to=timezone.now() + timezone.timedelta(days=10),
                                           discount=20,
                                           category=category_coupon)

    def test_apply_coupon_success(self):
        """
        Checking successfully applying coupon and adding it to profile
        """
        client = Client()
        client.login(username=self.user.username, password='password')

        self.coupon.valid_to = timezone.now() + timezone.timedelta(days=10)  # make coupon as valid
        self.coupon.save()

        self.response = client.post(reverse('coupons:apply_coupon'),
                                    {'code': self.coupon.code},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)  # convert Json to python dict

        self.assertIn('coupon_discount', content_response)
        self.assertEqual(content_response['coupon_discount'], str(self.coupon.discount / 100))

        session = self.response.wsgi_request.session  # get session from request, got from response
        self.assertIn(('coupon_id', self.coupon.pk), session.items())  # check whether coupon id is in session
        # check whether coupon is in profile coupons
        self.assertIn(self.coupon, self.profile.coupons.all())

    def test_apply_coupon_fail(self):
        """
        Checking applying coupon, when coupon is invalid
        """
        self.coupon.valid_to = timezone.now() - timezone.timedelta(days=5)  # make coupon as invalid
        self.coupon.save()

        client = Client()
        client.login(username=self.user.username, password='password')

        self.response = client.post(reverse('coupons:apply_coupon'),
                                    {'code': self.coupon.code},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})
        self.assertIsInstance(self.response, JsonResponse)
        content_response = json.loads(self.response.content)  # convert Json to python dict
        self.assertIn('form_errors', content_response)

        session = self.response.wsgi_request.session
        self.assertIsNone(session['coupon_id'])

    def test_cancel_coupon(self):
        """
        Checking successfully cancel coupon applying
        """
        client = Client()
        client.login(username=self.user.username, password='password')
        session = client.session
        session.update({'coupon_id': self.coupon.pk})
        session.save()

        client.login(username=self.user.username, password='password')

        self.response = client.post(reverse('coupons:cancel_coupon'),
                                    {'code': self.coupon.code},
                                    **{'HTTP_X-REQUESTED-WITH': 'XMLHttpRequest'})

        self.assertIsInstance(self.response, JsonResponse)
        response_content = json.loads(self.response.content)

        self.assertIn('coupon_discount', response_content)
        self.assertEqual(response_content['coupon_discount'], str(self.coupon.discount / 100))

        self.assertNotIn(self.coupon, self.profile.coupons.all())
        self.assertNotIn('coupon_id', self.response.wsgi_request.session)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
