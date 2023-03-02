from django.db import models

from django.conf import settings


class Profile(models.Model):
    """
    Модель пользователя сайта
    """

    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(choices=GENDER, max_length=6, blank=True)
    about = models.TextField(max_length=255, blank=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Profile "{self.user.username}"'