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
        Проверка сигнала, который удаляет папку с размещенным внутри фото пользователя,
        а также встроенного пользователя user при удалении объекта Profile
        """
        self.user = User.objects.create_user(username='testuser', first_name='Test', last_name='User')
        self.profile = Profile.objects.create(user=self.user)

        # путь к фото профиля
        photo_path = get_profile_photo_path(self.profile, 'photo_profile.jpg')
        self.profile.photo = os.path.join(settings.MEDIA_ROOT, photo_path)

        # создание в системе папки для тестового "фото" для профиля и создание самого файла "фото"
        run(['mkdir', '-p', f'{settings.MEDIA_ROOT}users/user_{self.user.get_full_name()}'])
        run(['touch', f'{os.path.join(settings.MEDIA_ROOT, photo_path)}'])

        # симуляция коннекта сигнала с отправителем сигнала
        with patch('account.signals.delete_profile_with_relative_user', autospec=True) as mocked_handler:
            post_delete.connect(mocked_handler, sender=Profile)
            self.profile.delete()  # действие, приводящее к отправке сигнала

        # кол-во вызовов сигнала должна быть не больше 1
        # экземпляры user и profile должны удалится из БД (id -> None)
        self.assertEqual(mocked_handler.call_count, 1)
        self.assertIsNone(self.user.pk)
        self.assertIsNone(self.profile.pk)
