from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.ProductCategoryViewSet, basename='product_category')
router.register(r'properties', views.PropertyViewSet, basename='product_property')
router.register(r'manufacturers', views.ManufacturerViewSet, basename='product_manufacturer')

app_name = 'goods_api'

urlpatterns = router.urls
