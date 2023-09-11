from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductList)
router.register(r'products_categories', views.ProductCategoryList)
router.register(r'products_properties', views.PropertiesList)

app_name = 'goods_api'

urlpatterns = router.urls
