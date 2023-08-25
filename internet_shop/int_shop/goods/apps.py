from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class GoodsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goods'

    def ready(self):
        from . import signals
        from goods.models import Property, Category
        # cache invalidate while creating or deleting new property category or deleting product category
        post_save.connect(receiver=signals.invalidate_properties_cache, sender=Property)
        post_delete.connect(receiver=signals.invalidate_properties_cache, sender=Category)
        post_delete.connect(receiver=signals.invalidate_properties_cache, sender=Property)
