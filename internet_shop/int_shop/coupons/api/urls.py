from django.urls import path
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import SchemaGenerator, get_schema_view

from . import views

coreapi_view_schema = get_schema_view(title='Coupons API',
                                      url='/api/coupons/',
                                      urlconf='coupons.api.urls',
                                      renderer_classes=[CoreJSONRenderer],
                                      generator_class=SchemaGenerator,
                                      description='API for coupons, which can be applied to cart')

router = DefaultRouter()
router.register(r'coupon', views.CouponViewSet, basename='coupon')
router.register(r'category', views.CouponCategoryViewSet, basename='category')

app_name = 'coupons_api'

urlpatterns = [
    path('schema', coreapi_view_schema),
]

urlpatterns += router.urls
