import base64
import os
import shutil
import sys
from decimal import Decimal
from io import BytesIO
from random import randint
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.urls.exceptions import NoReverseMatch
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase

from account.api.serializers import ProfileSerializer
from account.models import Profile
from goods.api.serializers import ProductSerializer
from goods.models import Favorite, Product, Category, Manufacturer


class TestAccountAPI(APITestCase):
    """
    Testing API for account application
    """

    def setUp(self):
        random_number = randint(1, 50)
        settings.CELERY_TASK_ALWAYS_EAGER = True
        self.main_user = User.objects.create_user(username='admin_user',
                                                  password='password',
                                                  first_name='Admin',
                                                  last_name='User',
                                                  email='admin@example.com')
        self.main_user.set_password('password')
        self.token = Token.objects.get(user__username=self.main_user.username)

        self.user1 = User.objects.create_user(username='test_user1',
                                              first_name='Name',
                                              last_name='Surname')
        
        self.user2 = User.objects.create_user(username='test_user2')
        self.user3 = User.objects.create_user(username='test_user3')

        self.profile1 = Profile.objects.create(user=self.main_user,
                                               gender='M',
                                               about='About')
        
        self.profile2 = Profile.objects.create(user=self.user1,
                                               gender='M',
                                               phone_number='+380969998877')
        
        self.profile3 = Profile.objects.create(user=self.user2)
        self.profile4 = Profile.objects.create(user=self.user3)

        category = Category.objects.create(name=f'Category_{random_number}',
                                           slug=f'category-{random_number}')
        
        manufacturer = Manufacturer.objects.create(name=f'Manufacturer_{random_number}',
                                                   slug=f'manufacturer_{random_number}',
                                                   description='Description')
        
        self.product = Product.objects.create(name=f'Product_{random_number}',
                                              slug=f'product_{random_number}',
                                              manufacturer=manufacturer,
                                              price=Decimal('300.25'),
                                              description='Description',
                                              category=category)

        Favorite.objects.create(profile=self.profile2)
        self.profile2.profile_favorite.product.add(self.product)

        self.client = APIClient()

    def test_get_profile_list_for_authorized_staff_users_only(self):
        """
        Checking, whether access to profile list allows just for authorized staff users
        """
        response = self.client.get(reverse('account_api:profile-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('account_api:profile-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.main_user.is_staff = True  # make user as staff
        self.main_user.save()
        response = self.client.get(reverse('account_api:profile-list'))
        view = response.renderer_context['view']
        serializer = ProfileSerializer(instance=[self.profile1, self.profile2, self.profile3, self.profile4],
                                       many=True)
        actual_result = response.data['results'] if settings.REST_FRAMEWORK.get(
            'DEFAULT_PAGINATION_CLASS') or hasattr(view, 'pagination_class') else response.data
        expected_result = serializer.data

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(actual_result), 4)
        self.assertListEqual(actual_result, expected_result)

    def test_create_profile_for_anyone(self):
        """
        Checking, whether can anyone to create profile
        """
        profile_data = {
            'username': 'another_user',
            'email': 'another_user@example.com',
            'first_name': 'Another',
            'last_name': 'User',
            'password1': 'strong_password',
            'password2': 'strong_password',
            'gender': 'M',
            'about': 'Some about',
            'phone_number': '+380661111111'
        }

        response = self.client.post(reverse('account_api:profile-list'), data=profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Profile.objects.filter(user__username='another_user').exists())

        created_profile_data = Profile.objects.get(user__username='another_user').__dict__
        for field, value in created_profile_data.items():
            if field in profile_data:
                self.assertEqual(value, profile_data[field])

    def test_delete_own_profile(self):
        """
        Checking delete own profile from the system.
        Profile can be deleted only it by its owner.
        """
        profile_token = Token.objects.get(user__username=self.user1.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {profile_token.key}')
        response = self.client.delete(reverse('account_api:profile-delete_own_profile'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(ObjectDoesNotExist):
            self.profile1.refresh_from_db()
            self.user1.refresh_from_db()

    def test_partial_update_profile(self):
        """
        Checking partial update profile information including also info of built-in user
        """
        profile_data = {
            'gender': 'F',
            'about': 'Some about additional info',
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.patch(reverse('account_api:profile-detail', args=(self.profile1.pk,)),
                                     data=profile_data,
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.gender, profile_data['gender'])
        self.assertEqual(self.profile1.about, profile_data['about'])

    def test_full_update_profile(self):
        """
        Checking full update profile information including also info of built-in user
        """
        new_profile_data = {
            'username': self.main_user.username,
            'date_of_birth': '1999-09-15',
            'gender': 'F',
            'about': 'Info about me!',
            'phone_number': '+380671111111',
            'first_name': self.main_user.first_name,
            'last_name': self.main_user.last_name,
            'email': 'admin@example.com'
        }

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.put(reverse('account_api:profile-detail', args=(self.profile1.pk,)),
                                   data=new_profile_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.main_user.refresh_from_db()
        for field, value in self.profile1.__dict__.items():
            if field in new_profile_data and field != 'date_of_birth':
                self.assertEqual(value, new_profile_data[field])
            elif field == 'date_of_birth':
                self.assertEqual(value, timezone.datetime.strptime(new_profile_data[field], '%Y-%m-%d').date())

    def test_reset_password_success(self):
        """
        Checking possibility to reset user's account password with success outcome
        """
        self.main_user.is_staff = True
        self.main_user.save()
        # receive email to console
        current_email_backend = settings.EMAIL_BACKEND
        if current_email_backend != 'django.core.mail.backends.console.EmailBackend':
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

        # save received email about reset password from console to the file
        orig_stdout = sys.stdout
        sys.stdout = open('reset_password_email.txt', 'w', encoding='utf-8')
        # send email first
        response = self.client.post(reverse('account_api:reset_user_password'),
                                    data={'email': self.main_user.email},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sys.stdout.close()
        sys.stdout = orig_stdout  # return original stdout

        # iterate by email text and save uid and token for set new password
        token = uid = None
        for line in open('reset_password_email.txt', 'r', encoding='utf-8').readlines():
            if line.strip().startswith('Token for reset password'):
                split_line = line.strip().split('"')
                token, uid = split_line[3], split_line[7]
                break
        # send received uid, token and new password
        response = self.client.post(reverse('account_api:reset_user_password'),
                                    data={'uid': uid, 'token': token, 'password': 'strong_password'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # make base64 string with new password  for base authentication
        # and try to get list profiles, which can be got only by staff users
        encode64_data = base64.b64encode(force_bytes(f'{self.main_user.username}:strong_password'))
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {force_str(encode64_data)}')
        response = self.client.get(reverse('account_api:profile-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        os.remove('reset_password_email.txt')
        settings.EMAIL_BACKEND = current_email_backend  # return email backend to settings

    def test_reset_password_fail(self):
        """
        Checking possibility to reset user's account password with unsuccessfully outcome
        """
        self.main_user.is_staff = True
        self.main_user.save()
        # receive email to console
        current_email_backend = settings.EMAIL_BACKEND
        if current_email_backend != 'django.core.mail.backends.console.EmailBackend':
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

        # make token term as expired
        current_password_reset_timeout = settings.PASSWORD_RESET_TIMEOUT
        settings.PASSWORD_RESET_TIMEOUT = -1

        # save received email about reset password from console to the file
        orig_stdout = sys.stdout
        sys.stdout = open('reset_password_email.txt', 'w', encoding='utf-8')
        # send email first
        response = self.client.post(reverse('account_api:reset_user_password'),
                                    data={'email': self.main_user.email},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sys.stdout.close()
        sys.stdout = orig_stdout  # return original stdout

        # iterate by email text and save uid and token for set new password
        token = uid = None
        for line in open('reset_password_email.txt', 'r', encoding='utf-8').readlines():
            if line.strip().startswith('Token for reset password'):
                split_line = line.strip().split('"')
                token, uid = split_line[3], split_line[7]
                break
        # send received uid, token and new password
        response = self.client.post(reverse('account_api:reset_user_password'),
                                    data={'uid': uid, 'token': token, 'password': 'strong_password'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        os.remove('reset_password_email.txt')
        settings.EMAIL_BACKEND = current_email_backend  # return email backend to settings
        settings.PASSWORD_RESET_TIMEOUT = current_password_reset_timeout

    def test_get_profile_info(self):
        """
        Checking getting profile info by profile owner
        """
        token = Token.objects.get(user__username=self.user1.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get(reverse('account_api:profile-profile_detail'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = ProfileSerializer(instance=self.profile2)
        actual_result = response.data
        expected_result = serializer.data
        self.assertDictEqual(actual_result, expected_result)

    def test_get_list_favorites(self):
        """
        Checking getting favorites profile's products
        """
        token = Token.objects.get(user__username=self.user1.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get(reverse('account_api:profile-favorite_products_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProductSerializer(instance=self.product)
        actual_result = response.data
        expected_result = serializer.data
        self.assertEqual(len(actual_result), 1)
        self.assertDictEqual(actual_result[0], expected_result)

    @patch('account.api.views.redis')
    def test_get_list_watched_products(self, mock_redis):
        """
        Checking getting watched products of profile
        """
        mock_redis.smembers.return_value = {self.product.pk, }

        token = Token.objects.get(user__username=self.user1.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get(reverse('account_api:profile-watched_products_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProductSerializer(instance=self.product)
        actual_result = response.data
        expected_result = serializer.data
        self.assertEqual(len(actual_result), 1)
        self.assertDictEqual(actual_result[0], expected_result)

    def test_add_or_remove_favorite_product(self):
        """
        Checking whether user can add product into own favorites or remove product from favorites
        """
        token = Token.objects.get(user__username=self.user1.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        # add product into favorites
        response = self.client.post(
            reverse('account_api:profile-add_remove_product_favorite',
                    kwargs={'product_pk': self.product.pk, 'act': 'add'}), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.profile2.profile_favorite.product.count(), 1)
        self.assertEqual(self.product, self.profile2.profile_favorite.product.first())

        # remove product from favorites
        response = self.client.post(
            reverse('account_api:profile-add_remove_product_favorite',
                    kwargs={'product_pk': self.product.pk, 'act': 'remove'}), format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.profile2.profile_favorite.product.count(), 0)

        # pass neither `remove` nor `add` in `act` param
        with self.assertRaises(NoReverseMatch):
            self.client.post(reverse('account_api:profile-add_remove_product_favorite',
                                     kwargs={'product_pk': self.product.pk, 'act': 'other'}), format='json')

    def test_check_user_is_authenticate(self):
        """
        Checking how user can check whether he/she credentials is correct
        """
        token = Token.objects.get(user__username=self.main_user.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get(reverse('account_api:check_user_auth'))
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # credentials are wrong
        self.client.credentials(username=self.main_user.username, password='pass')
        response = self.client.get(reverse('account_api:check_user_auth'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_photo_for_profile_account(self):
        """
        Checking uploading photo to profile's account
        """
        token = Token.objects.get(user__username=self.main_user.username)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        image_name = 'avatar.png'
        image = open('./account/api/tests/avatar.png', 'rb')
        image_as_bytes = BytesIO(image.read())

        response = self.client.put(reverse('account_api:upload_photo', args=(image_name,)),
                                   data={'photo': image_as_bytes},
                                   format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(
            f'/media/users/user_{self.main_user.get_full_name()}/{image_name}',
            self.profile1.photo.url.replace('%20', ' ')
        )
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'users/user_{self.main_user.get_full_name()}'))

    def tearDown(self):
        settings.CELERY_TASK_ALWAYS_EAGER = False
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, f'products/product_{self.product}'))
