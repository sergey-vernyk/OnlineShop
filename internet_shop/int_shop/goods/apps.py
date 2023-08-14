from django.apps import AppConfig
from django.db.models.signals import post_save


class GoodsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goods'

    def ready(self):
        from . import signals
        from goods.models import Property, PropertyCategory
        # cache invalidate while created new product property or new property category
        post_save.connect(receiver=signals.invalidate_properties_cache, sender=Property)
        post_save.connect(receiver=signals.invalidate_properties_cache, sender=PropertyCategory)
