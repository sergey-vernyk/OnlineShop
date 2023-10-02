from django.urls import path
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import SchemaGenerator, get_schema_view

from . import views

view_schema = get_schema_view(title='Coupons API',
                              url='/api/coupons/',
                              urlconf='coupons.api.urls',
                              renderer_classes=[CoreJSONRenderer],
                              generator_class=SchemaGenerator,
                              authentication_classes=[BasicAuthentication, TokenAuthentication],
                              description='API for coupons, which can be applied to cart')

router = DefaultRouter()
router.register(r'coupons', views.CouponViewSet, basename='coupon')
router.register(r'categories', views.CouponCategoryViewSet, basename='category')

app_name = 'coupons_api'

urlpatterns = [
    path('schema', view_schema),
]

urlpatterns += router.urls
