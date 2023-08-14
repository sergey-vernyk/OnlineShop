from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage for media files (products pics, user photos) in the AWS
    """
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    bucket_name = 'onlineshopproj-static-media'
