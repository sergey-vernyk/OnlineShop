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
from account.forms import ForgotPasswordForm


class TestAccountViews(TestCase):
    instance = None
    request = None
    client = None

    @classmethod
    def setUpClass(cls):
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
        Проверка регистрации пользователя, когда все поля корректно заполнены
        """
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
        }

        response = self.client.post(reverse('register_user'), data=register_data)
        request = response.wsgi_request
        self.assertRedirects(response, reverse('login'))  # переадресация на страницу входа в систему
        profile = Profile.objects.filter(user__username='testuser').get()
        self.assertTrue(profile)

        if profile:
            favorite = Favorite.objects.filter(profile=profile).exists()
            self.assertTrue(favorite)

        # проверка выдачи сообщения пользователю после успешной регистрации
        messages = get_messages(request)
        for n, s in enumerate(messages, 1):
            if n == 1:
                self.assertEqual(
                    s.message,
                    'Please, check your email! You have to receive email with instruction for activate account'
                )

    def test_register_user_fail(self):
        """
        Проверка рендера страницы с ошибками формы,
        когда какие-либо поля формы не заполнены корректно
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
        }

        response = self.client.post(reverse('register_user'), data=register_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.context['form'])
        # поля должны быть обязательно заполнены
        self.assertFormError(response.context['form'], 'email', ['This field is required.'])
        self.assertFormError(response.context['form'], 'password2', ['This field is required.'])

    def test_activate_user_account(self):
        """
        Проверка активации аккаунта зарегистрированного пользователя
        после перехода пользователя по ссылке в его email
        """
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
        }

        # тест с успешной активацией аккаунта
        register_response = self.client.post(reverse('register_user'), data=register_data)
        request = register_response.wsgi_request
        self.assertRedirects(register_response, reverse('login'))  # переадресация на страницу входа в систему
        user = Profile.objects.get(user__username='testuser').user

        # данные для активации пользователя
        uid64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_account_token.make_token(user)

        activate_response = activate_user_account(request, uid64, token)
        activate_response.client = self.client
        self.assertRedirects(activate_response, reverse('login'))  # переход на страницу входа после успешной активации

        user.refresh_from_db(fields=['is_active'])  # получение обновленных данных в БД
        self.assertTrue(user.is_active)

        messages = get_messages(request)
        for n, s in enumerate(messages, 1):
            if n == 2:
                self.assertEqual(
                    s.message, 'Thank you for your email confirmation. Now you can login your account'
                )

        # тесты с безуспешной активацией (неверный токен или uidb64)
        user_activate_data = {
            'wrong_token': {
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': 'bvjowebvbwoevoweonhcfwow'  # рандомный токен
            },
            'wrong_uidb64': {
                'uidb64': urlsafe_base64_encode(force_bytes(154)),  # рандомный id пользователя
                'token': activation_account_token.make_token(user)
            }
        }

        for data in user_activate_data.values():
            activate_response = activate_user_account(request, data['uidb64'], data['token'])
            activate_response.client = self.client
            request.profile = self.guest_profile  # профиль гостевого пользователя для главной страницы
            self.assertRedirects(activate_response, reverse('goods:product_list'))

            messages = get_messages(request)
            for n, s in enumerate(messages, 1):
                if n == 3 or n == 4:
                    self.assertEqual(
                        s.message, 'Activation link is invalid!'
                    )

    def test_context_data_detail_user_view(self):
        """
        Проверка данных в контексте для страниц с пользовательской информацией
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

        # добавление профилю оцененного им комментария
        # добавление профилю подарочной карты
        # добавление профилю товара в избранное
        self.profile.comments_liked.add(self.comment)
        self.card.profile = self.profile
        self.favorite.product.add(self.product1)

        self.instance = DetailUserView()
        # настройка экземпляра view и добавление ему объекта профиля
        self.instance.setup(self.request, **{'location': 'about'})
        setattr(self.instance, 'object', self.profile)
        context = self.instance.get_context_data()

        # проверка содержания в контексте ключей словарей и содержимого этих словарей при location 'about'
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

        # добавление в redis id товаров, которые "просмотрел" пользователь "profile"
        self.redis.sadd(f'profile_id:{self.profile.pk}', self.product1.pk)
        self.redis.sadd(f'profile_id:{self.profile.pk}', self.product2.pk)

        for key in ('present_cards', 'watched'):
            self.instance.setup(self.request, **{'location': key})
            context = self.instance.get_context_data()
            self.assertIn(key, context)
            # проверка содержимого словаря контекста
            if key == 'present_cards':
                self.assertIn(self.card, context['present_cards'])
            elif key == 'watched':
                self.assertIn(self.product1, context['watched'])
                self.assertIn(self.product2, context['watched'])

    def test_get_object_detail_user_view(self):
        """
        Проверка объекта, полученного DetailUserView,
        используя kwargs из URL
        """
        self.user = User.objects.create_user(username='testuser')
        self.profile = Profile.objects.create(user=self.user)
        self.instance = DetailUserView()
        # настройка экземпляра view и добавление ему запись в kwargs
        self.instance.setup(self.request, **{'customer': f'{self.user.username}'})
        self.assertEqual(self.instance.get_object(), self.profile)

    @tag('social_profiles')  # используя флаг --exclude-tag social_profiles -> этот тест запущен не будет
    def test_save_social_user_to_profile(self):
        """
        Проверка сохранения профиля пользователя,
        который вошел в систему через социальные сети
        """

        # Facebook
        # получение данных будущего профиля в json виде с API Facebook
        # ACCESS_FACEBOOK_USER_TOKEN user токен нужно периодически обновлять, когда срок его действия заканчивается
        # https://developers.facebook.com/tools/explorer - ссылка для получения нового токена для тестов
        response = requests.post(f'https://graph.facebook.com/v16.0/me?fields=id%2Cname%2Cbirthday%2Cgender'
                                 f'%2Cpicture.width(80).height(80)%2Cemail&'
                                 f'access_token={settings.ACCESS_FACEBOOK_USER_TOKEN}').json()
        # новый встроенный пользователь для профиля из данных ответа
        new_user = User.objects.create_user(username=response['name'].replace(' ', ''),
                                            email=response['email'],
                                            first_name=response['name'].split()[0],
                                            last_name=response['name'].split()[1])
        # проверяемая функция
        save_social_user_to_profile(backend=FacebookOAuth2, response=response, user=new_user, is_new=True)
        profile = get_object_or_404(Profile, user__username=new_user.username)
        # проверка, что профиль был создан с соответствующими данными
        self.assertTrue(profile)
        self.assertEqual(profile.gender, response['gender'][0].title())
        self.assertTrue(profile.photo.url)
        self.assertEqual(profile.date_of_birth, datetime.strptime(response['birthday'], '%m/%d/%Y').date())
        profile.delete()  # удаления профиля, для теста авторизации через Google

        # Google
        # BEARER_AUTHORIZATION_TOKEN_GOOGLE нужно периодически обновлять, когда срок его действия заканчивается
        # https://developers.google.com/oauthplayground/ - ссылка для обновления Bearer токена для тестов
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo',
                                headers={
                                    'Authorization': f'Bearer {settings.BEARER_AUTHORIZATION_TOKEN_GOOGLE}'}).json()
        # добавление в ответ токена авторизации и id аккаунта пользователя
        response.update(token_type='Bearer',
                        access_token=settings.BEARER_AUTHORIZATION_TOKEN_GOOGLE,
                        sub=response['id'])

        new_user = User.objects.create_user(username=response['name'].replace(' ', ''),
                                            email=response['email'],
                                            first_name=response['given_name'],
                                            last_name=response['family_name'])
        # проверяемая функция
        save_social_user_to_profile(backend=GoogleOAuth2, response=response, user=new_user, is_new=True)
        profile = get_object_or_404(Profile, user__username=new_user.username)
        # проверка, что профиль был создан с соответствующими данными
        self.assertTrue(profile)
        self.assertTrue(profile.photo.url)
        self.assertEqual(profile.user.email, response['email'])
        profile.delete()

    def test_remember_me_checkbox_in_login_page(self):
        """
        Проверка функции "запомнить меня" на странице входа в систему
        """
        user = User.objects.create_user(username='testuser', password='password')
        user.set_password('password')
        profile = Profile.objects.create(user=user)
        Favorite.objects.create(profile=profile)

        login_data = {'username': profile.user.username, 'password': 'password', 'remember': True}
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.wsgi_request.session.get_expiry_age(), 1209600)  # время жизни сессии 14 дней
        self.assertRedirects(response, reverse('goods:product_list'))  # после успешного входа в систему - переадресация

        login_data.update(remember=False)  # "переключаем" checkbox Remember me
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.wsgi_request.session.get_expiry_age(), 1200)  # время жизни сессии 20 минут
        self.assertRedirects(response, reverse('goods:product_list'))

    def test_display_massage_after_send_email_for_password_reset(self):
        """
        Проверка вывода сообщения на страницу ввода email,
        после успешной отправки введенного email на сервер
        для сброса пароля учетной записи
        """
        self.user = User.objects.create_user(username='testuser', email='example@example.com', password='password')
        response = self.client.post(reverse('password_reset'), data={'email': self.user.email})
        request = response.wsgi_request

        messages = get_messages(request)
        for n, s in enumerate(messages, 1):
            if n == 5:
                self.assertEqual(
                    s.message, f"We've emailed you instructions for setting your password. "
                               f"If you don't receive an email, please make sure you've entered the"
                               f" address you registered with")

    @classmethod
    def tearDownClass(cls):
        settings.CELERY_TASK_ALWAYS_EAGER = False
