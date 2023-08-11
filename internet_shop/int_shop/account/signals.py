import os
import shutil

import boto3
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from account.models import Profile
from common.storage_backends import MediaStorage


@receiver(signal=post_delete, sender=Profile)
def delete_profile_with_relative_user(sender, instance: Profile, *args, **kwargs):
    """
    Delete profile's photo from AWS Bucket, directory with photo from media root
    and delete built-in instance User, which linked with  custom profile instance
    """
    if isinstance(instance.photo.storage, MediaStorage):
        aws_image_key = f'media/{instance.photo.name}'
        aws_s3_bucket = MediaStorage().bucket_name
        client = boto3.client('s3')
        client.delete_object(Bucket=aws_s3_bucket, Key=aws_image_key)
    else:
        # delete directory with profile's photo from file system, if user has added own photo during registration
        # delete built-in User instance, linked with custom profile
        if instance.photo.name:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'users', f'user_{instance.user.get_full_name()}'))
    instance.user.delete()
