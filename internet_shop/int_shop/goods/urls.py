from django.urls import path
from . import views

app_name = 'goods'
urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('goods/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('goods/<int:product_pk>/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
