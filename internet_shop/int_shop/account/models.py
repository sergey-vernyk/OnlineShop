from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from coupons.models import Coupon


def get_profile_photo_path(instance, filename) -> str:
    """
    Return path for save user's photo
    """
    return f'users/user_{instance.user.get_full_name()}/{filename}'


class Profile(models.Model):
    """
    Custom user's site model.
    """

    GENDER = (
        ('M', _('Male')),
        ('F', _('Female')),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_('User'))
    date_of_birth = models.DateField(blank=True, null=True, verbose_name=_('Birth date'))
    gender = models.CharField(choices=GENDER, max_length=6, blank=True, verbose_name=_('Gender'))
    about = models.TextField(max_length=255, blank=True, verbose_name=_('About'))
    photo = models.ImageField(upload_to=get_profile_photo_path, blank=True, max_length=500, verbose_name=_('Photo'))
    phone_number = models.CharField(max_length=15, blank=True, verbose_name=_('Phone number'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Created'))
    email_confirm = models.BooleanField(default=False, verbose_name=_('Email confirm'))
    coupons = models.ManyToManyField(Coupon, related_name='profile_coupons', blank=True, verbose_name=_('Coupons'))

    @property
    def email(self):
        return f'{self.user.email}'

    def __str__(self):
        return f'Profile "{self.user.username}"'

    class Meta:
        ordering = ('user_id',)
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')
