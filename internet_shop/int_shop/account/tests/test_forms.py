import json
from unittest.mock import patch

import redis
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.shortcuts import reverse
from django.test import TestCase, Client, RequestFactory

from account.forms import LoginForm, RegisterUserForm, ForgotPasswordForm
from account.models import Profile
from goods.models import Favorite


class TestAccountForms(TestCase):
    """
    Testing forms for the account application
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='password', email='example@example.com')
        self.profile = Profile.objects.create(user=self.user)
        Favorite.objects.create(profile=self.profile)
        self.user.set_password('password')
        self.client = Client()
        self.factory = RequestFactory()

        redis_instance = redis.StrictRedis(host=settings.REDIS_HOST,
                                           port=settings.REDIS_PORT,
                                           db=settings.REDIS_DB_NUM,
                                           charset='utf-8',
                                           decode_responses=True,
                                           socket_timeout=30)

        redis_patcher = patch('common.moduls_init.redis', redis_instance)
        self.redis = redis_patcher.start()

        self.captcha_text = 'AAA111'

    def test_successfully_login(self):
        """
        Checking successfully login while entering correct data (user exists in the system)
        """

        response = self.client.post(reverse('login'), {'username': self.user.username, 'password': 'password'})
        self.assertRedirects(response, reverse('goods:product_list'))  # redirecting to the main page
        self.assertTrue(self.user.is_authenticated)  # user is authenticated

        # email like username
        response = self.client.post(reverse('login'), {'username': self.user.email, 'password': 'password'})
        self.assertRedirects(response, reverse('goods:product_list'))
        self.assertTrue(self.user.is_authenticated)

    def test_enter_incorrect_data_to_login_form(self):
        """
        Checking if the user exists by it username or email
        """
        # user name doesn't exists
        request = self.factory.post(reverse('login'), {'username': 'no_exists_user', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='No_exists_user'))

        # email doesn't exists
        request = self.factory.post(reverse('login'), {'username': 'mail@mail.com', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='No_exists_user'))

        # invalid email
        request = self.factory.post(reverse('login'), {'username': 'mail@mail', 'password': 'password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('username', code='invalid'))

        # wrong password
        request = self.factory.post(reverse('login'), {'username': self.user.username, 'password': 'wrong-password'})
        instance = LoginForm(data=request.POST)
        self.assertTrue(instance.has_error('password', code='wrong_password'))

        # user is inactive
        self.user.is_active = False
        self.user.save()

        for name in (self.user.username, self.user.email):
            request = self.factory.post(reverse('login'), {'username': name, 'password': 'password'})
            instance = LoginForm(data=request.POST)
            self.assertTrue(instance.has_error('username', code='inactive_user'))

    def test_enter_exists_username_during_registration(self):
        """
        Checking the raise an error while submitting registration,
        when entered username, that exists in the system
        """
        request = self.factory.post(reverse('register_user'), {'username': self.user.username})
        instance = RegisterUserForm(request.POST)
        self.assertTrue(instance.has_error('username', code='exists_username'))  # that username exists

    def test_enter_exists_email_during_registration(self):
        """
        Checking the raise an error while submitting registration,
        when entered email, that exists in the system
        """
        request = self.factory.post(reverse('register_user'), {'email': self.user.email})
        instance = RegisterUserForm(request.POST)
        self.assertTrue(instance.has_error('email', code='exists_email'))  # that email exists

    def test_enter_not_exists_email_relative_with_register_user(self):
        """
        Checking the raise an error, when transmitting not exists email
        while user attempt to recover forgotten account password
        """
        request = self.factory.post(reverse('password_reset'), {'email': 'no_exists@example.com'})
        instance = ForgotPasswordForm(request.POST)
        self.assertTrue(instance.has_error('email', code='No_exists_user'))

    def test_clean_phone_number_register_user_form(self):
        """
        Checking whether a user entered correct phone number.
        Returns entered phone number or raise validation error otherwise
        """
        # phone number is correct
        request = self.factory.post(reverse('register_user'), {'phone_number': '+38 (097) 123 45 67'})
        instance = RegisterUserForm(request.POST)
        self.assertFalse(instance.has_error('phone_number'))

        # phone number has extra digit
        request = self.factory.post(reverse('register_user'), {'phone_number': '+38 (097) 123 45 672'})
        instance = RegisterUserForm(request.POST)
        error_data = instance.errors.as_json()
        data_json = json.loads(error_data)
        self.assertEqual(data_json['phone_number'][0]['message'], 'Invalid phone number')

        # phone number field wasn't filled
        request = self.factory.post(reverse('register_user'), {'phone_number': ''})
        instance = RegisterUserForm(request.POST)
        error_data = instance.errors.as_json()
        data_json = json.loads(error_data)
        self.assertEqual(data_json['phone_number'][0]['message'], 'This field must not be empty')

    def test_forgot_password_form(self):
        """
        Checking whether user can will reset his/her forgotten password
        """
        self.redis.hset(f'captcha:{self.captcha_text}', 'captcha_text', self.captcha_text)

        # successful send data for the reset password
        response = self.client.post(reverse('password_reset'),
                                    data={'email': self.user.email, 'captcha': 'AAA111'})
        self.assertRedirects(response, reverse('password_reset'))  # redirected to the same page

        request = response.wsgi_request
        messages = get_messages(request)
        for m in messages:
            # massage to frontend
            self.assertEqual(
                m.message, "We've emailed you instructions for setting your password. "
                           "If you don't receive an email, please make sure you've entered"
                           " the address you registered with"
            )

        # passing the not exists email in the system
        response = self.client.post(reverse('password_reset'),
                                    data={'email': 'mail@mail.com', 'captcha': 'AAA111'})
        self.assertEqual(response.status_code, 200)  # must return form with the error about wrong email
        self.assertFormError(response.context['form'], 'email',
                             ['Current email doesn\'t registered or user not active'])

        # passing the wrong captcha
        response = self.client.post(reverse('password_reset'),
                                    data={'email': self.user.email, 'captcha': 'HJE696'})
        self.assertEqual(response.status_code, 200)  # must return form with the error about wrong captcha
        self.assertFormError(response.context['form'], 'captcha', ['Captcha is not correct'])

    def tearDown(self) -> None:
        self.redis.hdel(f'captcha:{self.captcha_text}', 'captcha_text')
