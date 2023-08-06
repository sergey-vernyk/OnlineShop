import boto3
import os
import shutil

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from account.models import Profile
from common.storage_backends import MediaStorage


@receiver(signal=post_delete, sender=Profile)
def delete_profile_with_relative_user(sender, instance: Profile, *args, **kwargs):
    """
    Удаление фото профиля из aws, папки с фото профиля из media
    и связанного с профилем экземпляра User
    """
    if isinstance(instance.photo.storage, MediaStorage):
        aws_image_key = f'media/{instance.photo.name}'
        aws_s3_bucket = MediaStorage().bucket_name
        client = boto3.client('s3')
        client.delete_object(Bucket=aws_s3_bucket, Key=aws_image_key)
    else:
        # удаление папки с фото профиля с файловой системы, если пользователь добавлял свое фото при регистрации
        # удаление экземпляра пользователя встроенной модели User, связанной с профилем
        if instance.photo.name:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'users', f'user_{instance.user.get_full_name()}'))
    instance.user.delete()
