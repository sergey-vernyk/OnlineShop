from datetime import datetime
from io import BytesIO
from unittest import skip

import requests
from django.contrib.auth.models import User
from django.test import TestCase
from social_core.backends.google import GoogleOAuth2
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

    @skip
    def test_create_social_user_pipeline(self):  # TODO
        details = {
            'username': 'Username',
            'email': 'example@example.com',
            'fullname': 'Name Surname',
            'first_name': 'Name',
            'lst_name': 'Surname'
        }

        kwargs = {'username': 'Username', 'email': 'example@example.com'}

        create_user(strategy=DjangoStrategy, details=details, backend=GoogleOAuth2(DjangoStrategy), kwargs=kwargs)
