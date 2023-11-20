from io import BytesIO
from typing import BinaryIO, Union
from django.core import files
import requests

from account.models import Profile
from goods.models import Favorite

USER_FIELDS = ["username", "email", "first_name", "last_name"]


def get_image_from_url(url: str) -> BinaryIO:
    """
    Get image in bytes format by its URL.
    """
    resp = requests.get(url, timeout=10)
    bytes_inst = BytesIO()
    if resp.status_code == 200:
        bytes_inst.write(resp.content)

    return bytes_inst


def create_profile_from_social(**kwargs) -> None:
    """
    Create `Profile` instance, using API data from social media.
    """
    user_id = kwargs.get('user_id')
    gender = kwargs.get('gender')
    date_of_birth = kwargs.get('date_of_birth')
    photo_name = kwargs.get('photo_name')
    photo = kwargs.get('photo')

    profile = Profile.objects.create(user_id=user_id,
                                     gender=gender,
                                     date_of_birth=date_of_birth)

    profile.photo.save(photo_name, files.File(photo))  # save photo for profile

    Favorite.objects.create(profile=profile)  # create favorite instance for new profile


def create_user(strategy, details, backend, user=None, *args, **kwargs) -> Union[dict, None]:
    """
    Overriding method from `social_auth` pipelines.
    Add verification for a presence of a `.` (dot) in username
    and replace it with `_` (underscore), if `.` (dot) exists.
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
                new_v = v.replace('.', '_')  # creating a new username
                fields[k] = new_v
                break

    else:
        return

    return {"is_new": True, "user": strategy.create_user(**fields)}
