from django.urls import path, re_path
from . import views

app_name = 'cart_api'

urlpatterns = [
    path('items/', views.cart_items_view, name='cart_items'),
    re_path(r'^add/(?P<product_id>[0-9]+)(:?/(?P<quantity>[0-9]+))?/$', views.cart_add_or_update, name='add_to_cart'),
    re_path(r'^remove/(?P<product_id>[0-9]+)/$', views.cart_remove, name='remove_from_cart'),
]
