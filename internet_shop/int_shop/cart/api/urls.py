from django.urls import path, re_path
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import SchemaGenerator, get_schema_view

from . import views

# generate schema view for the app
coreapi_schema_view = get_schema_view(title='Cart API',
                                      url='/api/cart/',
                                      urlconf='cart.api.urls',
                                      generator_class=SchemaGenerator,
                                      renderer_classes=[CoreJSONRenderer],
                                      description='API for cart with products in order to purchase')

app_name = 'cart_api'

urlpatterns = [
    path('items/', views.cart_items, name='cart_items'),
    re_path(r'^add/(?P<product_id>[0-9]+)/(?P<quantity>[0-9]+)?/$', views.cart_add_or_update, name='add_to_cart'),
    re_path(r'^remove/(?P<product_id>[0-9]+)/$', views.cart_remove, name='remove_from_cart'),
    path('schema', coreapi_schema_view)
]
