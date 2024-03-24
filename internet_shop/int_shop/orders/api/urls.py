from django.urls import path
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view, SchemaGenerator
from django.conf import settings

from . import views

# generate schema view for the app
coreapi_schema_view = get_schema_view(title='Orders API',
                                      url=f'/api/{settings.REST_FRAMEWORK["DEFAULT_VERSION"]}/orders/',
                                      urlconf='orders.api.urls',
                                      generator_class=SchemaGenerator,
                                      renderer_classes=[CoreJSONRenderer],
                                      authentication_classes=[TokenAuthentication, BasicAuthentication],
                                      description='API for orders. '
                                                  'Contains with orders itself, order items and delivery')

router = DefaultRouter()
router.register(r'order', views.OrderViewSet, basename='order')
router.register(r'delivery', views.DeliveryViewSet, basename='delivery')

urlpatterns = [
    path('schema', coreapi_schema_view)
]

app_name = 'orders_api'

urlpatterns += router.urls
