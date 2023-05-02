from io import BytesIO
from typing import BinaryIO

import requests

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
