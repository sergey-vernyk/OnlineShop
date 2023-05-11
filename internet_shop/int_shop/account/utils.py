from io import BytesIO
from typing import BinaryIO
from django.core import files
import requests

from account.models import Profile
from goods.models import Favorite

USER_FIELDS = ["username", "email"]


def get_image_from_url(url: str) -> BinaryIO:
    """
    Получение изображения в формате байтов по его URL
    """
    resp = requests.get(url)
    bytes_inst = BytesIO()
    if resp.status_code == 200:
        bytes_inst.write(resp.content)

    return bytes_inst


def create_profile_from_social(**kwargs):
    """
    Создание экземпляра Profile, используя данные с API соц. сетей
    """
    user_id = kwargs.get('user_id')
    gender = kwargs.get('gender')
    date_of_birth = kwargs.get('date_of_birth')
    photo_name = kwargs.get('photo_name')
    photo = kwargs.get('photo')

    profile = Profile.objects.create(user_id=user_id,
                                     gender=gender,
                                     date_of_birth=date_of_birth)

    profile.photo.save(photo_name, files.File(photo))  # сохранение фото для профиля

    Favorite.objects.create(profile=profile)  # создание объекта избранного для нового профиля


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Переопределение метода из pipeline social_auth.
    Добавляется проверка на наличие точки "." в username
    и замена ее на "_", если она есть
    """
    if user:
        return {"is_new": False}

    fields = {
        name: kwargs.get(name, details.get(name))
        for name in backend.setting("USER_FIELDS", USER_FIELDS)
    }

    if fields:
        for k, v in fields.items():
            if k == 'username' and '.' in v:
                new_v = v.replace('.', '_')  # создание нового имени пользователя
                fields[k] = new_v

    else:
        return

    return {"is_new": True, "user": strategy.create_user(**fields)}
