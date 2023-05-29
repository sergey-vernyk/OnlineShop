from django.urls import path
from . import views

app_name = 'goods'
urlpatterns = [
    path('goods/<slug:category_slug>/filter/<int:page>/', views.FilterResultsView.as_view(),
         name='filter_results_list'),
    path('', views.ProductListView.as_view(), name='product_list'),
    path('goods/promotion/', views.promotion_list, name='promotion_list'),
    path('goods/<slug:category_slug>/promotion/', views.promotion_list, name='promotion_list_by_category'),
    path('goods/new/', views.new_list, name='new_list'),
    path('goods/<slug:category_slug>/new/', views.new_list, name='new_list_by_category'),
    path('goods/popular/', views.popular_list, name='popular_list'),
    path('goods/<slug:category_slug>/popular/', views.popular_list, name='popular_list_by_category'),
    path('goods/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('goods/<int:product_pk>/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('goods/ajax/add_remove_favorite/', views.add_or_remove_product_favorite,
         name='add_or_remove_product_favorite'),
    path('goods/ordering/<str:place>/<slug:category_slug>/<int:page>/', views.product_ordering,
         name='product_ordering'),
    path('goods/ajax/set_rating/', views.set_product_rating, name='set_product_rating'),
    path('goods/ajax/like_unlike_comment/', views.ProductDetailView.as_view(), name='like_unlike_comment'),

]
