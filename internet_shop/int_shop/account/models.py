from django.db import models
from django.conf import settings
from coupons.models import Coupon


def profile_photo_path(instance, filename):
    """
    Возвращает путь сохранения фото для каждого пользователя
    """
    return f'users/user_{instance.user.get_full_name()}/{filename}'


class Profile(models.Model):
    """
    Модель пользователя сайта
    """

    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(choices=GENDER, max_length=6, blank=True)
    about = models.TextField(max_length=255, blank=True)
    photo = models.ImageField(upload_to=profile_photo_path, blank=True, max_length=500)
    phone_number = models.CharField(max_length=15, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    email_confirm = models.BooleanField(default=False)
    coupons = models.ManyToManyField(Coupon, related_name='profile_coupons', blank=True)

    @property
    def email(self):
        return f'{self.user.email}'

    def __str__(self):
        return f'Profile "{self.user.username}"'
