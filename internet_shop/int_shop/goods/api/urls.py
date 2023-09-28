from django.urls import path
from rest_framework import routers
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import SchemaGenerator, get_schema_view

from . import views

# generate schema view for app
schema_view = get_schema_view(title='Goods API',
                              url='https://127.0.0.1:8001/api/goods/',
                              urlconf='goods.api.urls',
                              generator_class=SchemaGenerator,
                              renderer_classes=[CoreJSONRenderer],
                              authentication_classes=[TokenAuthentication, BasicAuthentication],
                              description='API for interactions with products, categories, manufacturers'
                                          'new, popular, promotional products.')

router = routers.DefaultRouter()
router.register(r'product', views.ProductViewSet, basename='product')
router.register(r'category', views.ProductCategoryViewSet, basename='product_category')
router.register(r'property', views.PropertyViewSet, basename='product_property')
router.register(r'manufacturer', views.ManufacturerViewSet, basename='product_manufacturer')

app_name = 'goods_api'

urlpatterns = [
    path('schema/', schema_view)
]

urlpatterns += router.urls
