from django.urls import path
from . import views

app_name = 'orders'
urlpatterns = [
    path('create/', views.OrderCreateView.as_view(), name='order_create'),
    path('created/', views.OrderConfirmedView.as_view(), name='order_created'),
]
