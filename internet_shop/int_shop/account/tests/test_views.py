import os
import shutil
from datetime import datetime
from decimal import Decimal
from random import randint
from unittest.mock import patch

import redis
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.shortcuts import reverse, get_object_or_404
from django.test import TestCase, Client, tag
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from social_core.backends.facebook import FacebookOAuth2
from social_core.backends.google import GoogleOAuth2

from account.models import Profile
from account.tokens import activation_account_token
from account.views import DetailUserView
from account.views import activate_user_account, save_social_user_to_profile
from coupons.models import Category as Coupon_Category, Coupon
from goods.models import (
    Favorite,
    Category,
    Manufacturer,
    Product,
    Comment
)
from orders.models import Order
from present_cards.models import Category as PresentCard_Category, PresentCard


class TestAccountViews(TestCase):
    """
    Testing account views
    """
    instance = None
    request = None
    client = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.CELERY_TASK_ALWAYS_EAGER = True
        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('account.views.DetailUserView', redis_instance)
        cls.redis = redis_patcher.start()

        cls.client = Client()
        guest_user = User.objects.create_user(username='guest_user', password='password')
        cls.guest_profile = Profile.objects.create(user=guest_user)

    def test_register_user_success(self):
        """
        Checking profile registration, when all fields are filling correct
        """
        captcha_text = 'AAA111'
        self.redis.hset(f'captcha:{captcha_text}', 'captcha_text', captcha_text)

        register_data = {
            'username': 'testuser',
            'email': 'example@example.com',
            'phone_number': '+380991234567',
            'password1': 'pg4B~H8PSP',
            'password2': 'pg4B~H8PSP',
            'first_name': 'Name',
            'last_name': 'Surname',
            'date_of_birth': datetime.strftime(datetime(1990, 1, 12).date(), '%d-%m-%Y'),
            'about': 'About Me',
            'gender': 'M',
            'captcha': 'AAA111'
        }

        response = self.client.post(reverse('register_user'), data=register_data)
        request = response.wsgi_request
        self.assertRedirects(response, reverse('login'))  # redirecting to the login page
        profile = Profile.objects.filter(user__username='testuser').get()
        self.assertTrue(profile)

        if profile:
            favorite = Favorite.objects.filter(profile=profile).exists()
            self.assertTrue(favorite)

        # checking getting message to user frontend after successfully registration
        messages = get_messages(request)
        for n, s in enumerate(messages, 1):
            if n == 1:
                self.assertEqual(
                    s.message,
                    'Please, check your email! You have to receive email with instruction for activate account'
                )

    def test_register_user_fail(self):
        """
        Checking display page with form errors,
        when whatever fields aren't filled correct
        """
        register_data = {
            'username': 'testuser',
            'email': '',
            'phone_number': '+380991234567',
            'password1': 'pg4B~H8PSP',
            'password2': '',
            'first_name': 'Name',
            'last_name': 'Surname',
            'date_of_birth': datetime.strftime(datetime(1990, 1, 12).date(), '%d-%m-%Y'),
            'about': 'About Me',
            'gender': 'M',
            'captcha': '',
        }

        response = self.client.post(reverse('register_user'), data=register_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context['form'])
        # fields must fill
        self.assertFormError(response.context['form'], 'email', ['This field is required.'])
        self.assertFormError(response.context['form'], 'password2', ['This field is required.'])
        self.assertFormError(response.context['form'], 'captcha', ['This field is required.'])

    def test_activate_user_account(self):
        """
        Checking registered user's account activation after user followed to link in his/her email
        """
        captcha_text = 'AAA111'
        self.redis.hset(f'captcha:{captcha_text}', 'captcha_text', captcha_text)

        register_data = {
            'username': 'testuser',
            'email': 'example@example.com',
            'phone_number': '+38 (099) 123 45 67',
            'password1': 'pg4B~H8PSP',
            'password2': 'pg4B~H8PSP',
            'first_name': 'Name',
            'last_name': 'Surname',
            'date_of_birth': datetime.strftime(datetime(1990, 1, 12).date(), '%d-%m-%Y'),
            'about': 'About Me',
            'gender': 'M',
            'captcha': 'AAA111'
        }

        # successfully activation test
        register_response = self.client.post(reverse('register_user'), data=register_data)
        request = register_response.wsgi_request
        self.assertRedirects(register_response, reverse('login'))  # redirecting to the login page
        user = Profile.objects.get(user__username='testuser').user

        # activation account data
        uid64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_account_token.make_token(user)

        activate_response = activate_user_account(request, uid64, token)
        activate_response.client = self.client
        # redirecting to the login page after successfully activation
        self.assertRedirects(activate_response, reverse('login'))

        user.refresh_from_db(fields=['is_active'])  # get updated data from DB
        self.assertTrue(user.is_active)

        messages = get_messages(request)
        for n, s in enumerate(messages, 1):
            if n == 2:
                self.assertEqual(
                    s.message, 'Thank you for your email confirmation. Now you can login your account'
                )

        # tests with not successfully activation (wrong token or uidb64)
        user_activate_data = {
            'wrong_token': {
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': 'bvjowebvbwoevoweonhcfwow'  # random token
            },
            'wrong_uidb64': {
                'uidb64': urlsafe_base64_encode(force_bytes(154)),  # random user id
                'token': activation_account_token.make_token(user)
            }
        }

        for data in user_activate_data.values():
            activate_response = activate_user_account(request, data['uidb64'], data['token'])
            activate_response.client = self.client
            request.profile = self.guest_profile  # set user profile for main page
            self.assertRedirects(activate_response, reverse('goods:product_list'))

            messages = get_messages(request)
            for n, s in enumerate(messages, 1):
                if n == 3 or n == 4:
                    self.assertEqual(
                        s.message, 'Activation link is invalid!'
                    )

    def test_context_data_detail_user_view(self):
        """
        Checking context data for pages with user information (orders, present cards,
        coupons, watched products, comments, favorites products, personal info)
        """
        random_number = randint(1, 50)

        self.user = User.objects.create_user(username='testuser')
        self.profile = Profile.objects.create(user=self.user)
        self.favorite = Favorite.objects.create(profile=self.profile)
        category_1 = Category.objects.create(name=f'Category_{random_number}', slug=f'category_{random_number}')
        category_2 = Category.objects.create(name=f'Category_{random_number + 1}', slug=f'category_{random_number + 1}')

        manufacturer1 = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                    slug=f'manufacturer_{random_number}',
                                                    description='Description')

        manufacturer2 = Manufacturer.objects.create(name=f'Manufacturer_{random_number + 1}',
                                                    slug=f'manufacturer_{random_number + 1}',
                                                    description='Description')

        self.product1 = Product.objects.create(name=f'Product_{random_number}',
                                               slug=f'product_{random_number}',
                                               manufacturer=manufacturer1,
                                               price=Decimal('300.25'),
                                               description='Description',
                                               category=category_1)

        self.product2 = Product.objects.create(name=f'Product_{random_number + 1}',
                                               slug=f'product_{random_number + 1}',
                                               manufacturer=manufacturer2,
                                               price=Decimal('650.45'),
                                               description='Description',
                                               category=category_2)

        category_coupon = Coupon_Category.objects.create(name='For men', slug='for-men')

        self.coupon = Coupon.objects.create(code=f'coupon_code_{random_number + 5}',
                                            valid_from=timezone.now(),
                                            valid_to=timezone.now() + timezone.timedelta(days=10),
                                            discount=20,
                                            category=category_coupon)

        category_card = PresentCard_Category.objects.create(name='For men', slug='for-men')

        self.card = PresentCard.objects.create(code=f'card_code_{random_number + 5}',
                                               valid_from=timezone.now(),
                                               valid_to=timezone.now() + timezone.timedelta(days=10),
                                               amount=250,
                                               from_name='From Name',
                                               from_email='email@example.com',
                                               to_name='To Name',
                                               to_email='example_2@example.com',
                                               category=category_card,
                                               profile=self.profile)

        self.order = Order.objects.create(first_name='Name',
                                          last_name='Surname',
                                          email='example@example.com',
                                          phone='+38 (099) 123 45 67',
                                          pay_method='Online',
                                          profile=self.profile,
                                          coupon=self.coupon,
                                          present_card=self.card)

        self.comment = Comment.objects.create(product=self.product1,
                                              profile=self.profile,
                                              user_name=self.profile.user.first_name,
                                              user_email=self.profile.user.email,
                                              body='Body of comment')

        # add a profile rated comment
        # add present card to profile
        # add product to profile's favorite
        self.profile.comments_liked.add(self.comment)
        self.card.profile = self.profile
        self.favorite.product.add(self.product1)

        self.instance = DetailUserView()
        # instance view setup and add to it profile instance
        self.instance.setup(self.request, **{'location': 'about'})
        setattr(self.instance, 'object', self.profile)
        context = self.instance.get_context_data()

        # checking keys and checking content in context content using "about" location
        for key in ('favorites', 'orders', 'coupons', 'comments'):
            self.assertIn(key, context)
            if key == 'favorite':
                self.assertIn(self.product1, context['favorite'])
            elif key == 'orders':
                self.assertIn(self.order, context['orders'])
            elif key == 'coupons':
                self.assertIn(self.coupon, context['coupons'])
            elif key == 'comments':
                self.assertIn(self.comment, context['comments'])

        # add products ids to redis, which "watched" profile
        self.redis.sadd(f'profile_id:{self.profile.pk}', self.product1.pk)
        self.redis.sadd(f'profile_id:{self.profile.pk}', self.product2.pk)

        for key in ('present_cards', 'watched'):
            self.instance.setup(self.request, **{'location': key})
            context = self.instance.get_context_data()
            self.assertIn(key, context)
            # checking content of content dict
            if key == 'present_cards':
                self.assertIn(self.card, context['present_cards'])
            elif key == 'watched':
                self.assertIn(self.product1, context['watched'])
                self.assertIn(self.product2, context['watched'])

        # delete directories, which were created in the file system while creating products
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product1.name}'))
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product2.name}'))

    def test_get_object_detail_user_view(self):
        """
        Checking object, received DetailUserView, using kwargs from URL
        """
        self.user = User.objects.create_user(username='testuser')
        self.profile = Profile.objects.create(user=self.user)
        self.instance = DetailUserView()
        # set up view instance and adding record to it kwargs
        self.instance.setup(self.request, **{'customer': f'{self.user.username}'})
        self.assertEqual(self.instance.get_object(), self.profile)

    @tag('social_profiles')  # using flag --exclude-tag social_profiles -> this test won't be run
    def test_save_social_user_to_profile(self):
        """
        Checking whether profile instance save, while login over social
        """

        # Facebook
        # getting data for future profile in json from Facebook API
        # ACCESS_FACEBOOK_USER_TOKEN have to refresh periodically, when its term was ended
        # https://developers.facebook.com/tools/explorer - link from receive new token for test
        response = requests.post(f'https://graph.facebook.com/v16.0/me?fields=id%2Cname%2Cbirthday%2Cgender'
                                 f'%2Cpicture.width(80).height(80)%2Cemail&'
                                 f'access_token={settings.ACCESS_FACEBOOK_USER_TOKEN}').json()
        # new build-in user for profile instance from response data
        new_user = User.objects.create_user(username=response['name'].replace(' ', ''),
                                            email=response['email'],
                                            first_name=response['name'].split()[0],
                                            last_name=response['name'].split()[1])
        # function being testing
        save_social_user_to_profile(backend=FacebookOAuth2, response=response, user=new_user, is_new=True)
        profile = get_object_or_404(Profile, user__username=new_user.username)
        # checking, that profile was created with appropriate data
        self.assertTrue(profile)
        self.assertEqual(profile.gender, response['gender'][0].title())
        self.assertTrue(profile.photo.url)
        self.assertEqual(profile.date_of_birth, datetime.strptime(response['birthday'], '%m/%d/%Y').date())
        profile.delete()  # deleting profile, for an authorization test through the Google

        # Google
        # BEARER_AUTHORIZATION_TOKEN_GOOGLE have to refresh periodically, when its term was ended
        # https://developers.google.com/oauthplayground/ - link for refresh Berer token for tests
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo',
                                headers={
                                    'Authorization': f'Bearer {settings.BEARER_AUTHORIZATION_TOKEN_GOOGLE}'}).json()
        # add authorization token and google account id to the response
        response.update(token_type='Bearer',
                        access_token=settings.BEARER_AUTHORIZATION_TOKEN_GOOGLE,
                        sub=response['id'])

        new_user = User.objects.create_user(username=response['name'].replace(' ', ''),
                                            email=response['email'],
                                            first_name=response['given_name'],
                                            last_name=response['family_name'])
        # function being testing
        save_social_user_to_profile(backend=GoogleOAuth2, response=response, user=new_user, is_new=True)
        profile = get_object_or_404(Profile, user__username=new_user.username)
        # checking, that profile was created with appropriate data
        self.assertTrue(profile)
        self.assertTrue(profile.photo.url)
        self.assertEqual(profile.user.email, response['email'])
        profile.delete()

    def test_remember_me_checkbox_in_login_page(self):
        """
        Checking "remember me" function on login page
        """
        user = User.objects.create_user(username='testuser', password='password')
        user.set_password('password')
        profile = Profile.objects.create(user=user)
        Favorite.objects.create(profile=profile)

        login_data = {'username': profile.user.username, 'password': 'password', 'remember': True}
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.wsgi_request.session.get_expiry_age(), 1209600)  # session lifetime is 14 days
        self.assertRedirects(response, reverse('goods:product_list'))  # redirection after successfully login

        login_data.update(remember=False)  # "toggle" checkbox "Remember me?"
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.wsgi_request.session.get_expiry_age(), 1200)  # session lifetime is 20 minutes
        self.assertRedirects(response, reverse('goods:product_list'))

    def test_display_massage_after_send_email_for_password_reset(self):
        """
        Checking displaying message on frontend page with email field,
        after successfully sent email address to reset account password
        """
        self.user = User.objects.create_user(username='testuser', email='example@example.com', password='password')
        response = self.client.post(reverse('password_reset'), data={'email': self.user.email})
        request = response.wsgi_request

        messages = get_messages(request)
        for n, s in enumerate(messages, 1):
            if n == 5:
                self.assertEqual(
                    s.message, "We've emailed you instructions for setting your password. "
                               "If you don't receive an email, please make sure you've entered the"
                               " address you registered with")

    @classmethod
    def tearDownClass(cls):
        settings.CELERY_TASK_ALWAYS_EAGER = False
        cls.redis.hget('captcha:aaa111', 'captcha_text')
        super().tearDownClass()
