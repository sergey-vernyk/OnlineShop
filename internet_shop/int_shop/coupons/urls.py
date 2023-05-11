from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('apply/ajax/', views.apply_coupon, name='apply_coupon'),
    path('cancel/ajax/', views.cancel_coupon, name='cancel_coupon')
]
