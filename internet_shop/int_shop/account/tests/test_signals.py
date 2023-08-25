import os
from django.conf import settings
from django.test import TestCase
from unittest.mock import patch
from django.db.models.signals import post_delete
from account.models import Profile, get_profile_photo_path
from django.contrib.auth.models import User
from subprocess import run


class TestAccountSignals(TestCase):
    def test_delete_profile_with_relative_user(self):
        """
        Checking the signal, which delete directory with profile photo,
        and delete built-in user while deleting Profile instance
        """
        self.user = User.objects.create_user(username='testuser', first_name='Test', last_name='User')
        self.profile = Profile.objects.create(user=self.user)

        # path to the profile photo
        photo_path = get_profile_photo_path(self.profile, 'photo_profile.jpg')
        self.profile.photo = os.path.join(settings.MEDIA_ROOT, photo_path)

        # create directory in the file system for test-photo for the profile and create "photo" file itself
        run(['mkdir', '-p', f'{settings.MEDIA_ROOT}users/user_{self.user.get_full_name()}'])
        run(['touch', f'{os.path.join(settings.MEDIA_ROOT, photo_path)}'])

        # simulate connecting the signal with transmitter of this signal
        with patch('account.signals.delete_profile_with_relative_user', autospec=True) as mocked_handler:
            post_delete.connect(mocked_handler, sender=Profile)
            self.profile.delete()  # action that leading to the signal send

        # number of callings of the signal must be not greater than 1
        # user and profile instances must delete from DB (id -> None)
        self.assertEqual(mocked_handler.call_count, 1)
        self.assertIsNone(self.user.pk)
        self.assertIsNone(self.profile.pk)
