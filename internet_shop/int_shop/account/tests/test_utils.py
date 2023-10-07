from datetime import datetime
from io import BytesIO

import requests
from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.test import RequestFactory, Client
from django.test import TestCase
from social_core.backends.facebook import FacebookOAuth2
from social_core.backends.google import GoogleOAuth2
from social_django.models import DjangoStorage
from social_django.strategy import DjangoStrategy

from account.models import Profile
from account.utils import get_image_from_url, create_profile_from_social, create_user
from goods.models import Favorite


class TestAccountUtilities(TestCase):
    """
    Testing utilities
    """
    bytes_inst = None
    image_url = None

    @classmethod
    def setUpTestData(cls):
        cls.image_url = 'https://drive.google.com/uc?export=download&id=1zy2M7o8supmIRqVCatzwYuaQGAcBEVAX'
        response = requests.get(cls.image_url)
        cls.bytes_inst = BytesIO()
        cls.image = cls.bytes_inst.write(response.content)

    def test_get_image_from_url(self):
        """
        Checking receiving image using link and
        convert this image to byte format
        """
        self.image = get_image_from_url(self.image_url)
        self.assertIsInstance(self.image, BytesIO)
        self.assertIsInstance(self.image.getvalue(), bytes)

    def test_create_profile_from_social(self):
        """
        Checking successfully creating profile from social data
        """
        kwargs = {
            'user_id': User.objects.create_user(username='testuser', first_name='Test', last_name='User').pk,
            'gender': 'M',
            'date_of_birth': datetime(day=12, month=5, year=1985).date(),
            'photo_name': 'social_photo.png',
            'photo': self.bytes_inst,
        }

        create_profile_from_social(**kwargs)

        self.assertTrue(Profile.objects.filter(user_id=kwargs['user_id']).exists())
        self.assertTrue(Favorite.objects.filter(profile=Profile.objects.get(user=kwargs['user_id'])))

    def test_create_social_user_pipeline(self):
        """
        Checking overriden pipeline, which create built-in user instance,
        and replace dot (.) in username with underscore (_)
        """

        details = {
            'username': 'superuser.123',
            'email': 'example@example.com',
            'fullname': 'Super User',
            'first_name': 'Super',
            'last_name': 'User'
        }

        kwargs = {
            'username': 'superuser.123',
            'email': 'example@example.com',
            'first_name': 'Super',
            'last_name': 'User'
        }

        self.client = Client()
        self.factory = RequestFactory()
        self.storage = DjangoStorage()

        # test to create user through Google
        request = self.factory.get(reverse('social:complete', kwargs={'backend': 'google-oauth2'}))
        request.session = self.client.session

        instance_strategy = DjangoStrategy(storage=self.storage, request=request)
        result = create_user(strategy=instance_strategy,
                             details=details,
                             backend=GoogleOAuth2(instance_strategy),
                             kwargs=kwargs)

        self.assertTrue(User.objects.filter(username='superuser_123').exists())
        created_user = User.objects.get(username='superuser_123')
        self.assertDictEqual(result, {'is_new': True, 'user': created_user})

        for field, value in created_user.__dict__.items():
            if field in details:
                if field == 'username':
                    self.assertEqual(value, details[field].replace('.', '_'))
                else:
                    self.assertEqual(value, details[field])

        # test to create user through Facebook
        request = self.factory.get(reverse('social:complete', kwargs={'backend': 'facebook'}))
        request.session = self.client.session

        instance_strategy = DjangoStrategy(storage=self.storage, request=request)
        result = create_user(strategy=instance_strategy,
                             details=details,
                             backend=FacebookOAuth2(instance_strategy),
                             kwargs=kwargs)

        self.assertTrue(User.objects.filter(username='superuser_123').exists())
        created_user = User.objects.get(username='superuser_123')
        self.assertDictEqual(result, {'is_new': True, 'user': created_user})

        for field, value in created_user.__dict__.items():
            if field in details:
                if field == 'username':
                    self.assertEqual(value, details[field].replace('.', '_'))
                else:
                    self.assertEqual(value, details[field])
