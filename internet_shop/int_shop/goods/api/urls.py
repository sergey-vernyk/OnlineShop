from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductSet, basename='product')
router.register(r'categories', views.ProductCategorySet, basename='product_category')
router.register(r'properties', views.PropertySet, basename='product_property')
router.register(r'manufacturers', views.ManufacturerSet, basename='product_manufacturer')

app_name = 'goods_api'

urlpatterns = router.urls
