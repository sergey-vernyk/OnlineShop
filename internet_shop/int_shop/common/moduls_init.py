import redis
from django.conf import settings

redis = redis.Redis(host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB_NUM,
                    username=settings.REDIS_USER,
                    password=settings.REDIS_PASSWORD)
