from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('detail/', views.cart_detail, name='cart_detail'),
    path('add/ajax/', views.cart_add, name='cart_add'),
    path('remove/ajax/', views.cart_remove, name='cart_remove'),
]
