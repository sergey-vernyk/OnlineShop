from django.urls import path
from . import views

app_name = 'goods'
urlpatterns = [
    path('goods/<slug:category_slug>/filter/<int:page>/', views.FilterResultsView.as_view(),
         name='filter_results_list'),
    path('', views.ProductListView.as_view(), name='product_list'),
    path('goods/promotions/', views.promotions_list, name='promotions_list'),
    path('goods/new/', views.new_list, name='new_list'),
    path('goods/<slug:category_slug>/popular/', views.popular_list, name='popular_list_by_category'),
    path('goods/popular/', views.popular_list, name='popular_list'),
    path('goods/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('goods/<int:product_pk>/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('goods/favorites/<str:username>/', views.FavoriteListView.as_view(),
         name='user_product_favorites_list'),
    path('goods/favorites/<str:action>/<int:product_pk>', views.add_or_remove_product_favorite,
         name='add_or_remove_product_favorite'),

]
