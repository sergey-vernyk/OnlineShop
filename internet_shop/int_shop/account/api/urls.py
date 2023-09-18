from django.urls import path, re_path
from rest_framework import routers
from rest_framework.authtoken import views as auth_views

from . import views

router = routers.DefaultRouter()
router.register(r'profile', views.AccountViewSet, basename='profile')

app_name = 'account_api'

urlpatterns = [
    path('auth/', views.auth_user, name='auth'),
    re_path(r'^upload/(?P<filename>[^/]+)/(?P<instance_pk>[0-9]+)/$', views.FileUploadView.as_view(),
            name='upload_image'),
    path('reset_password/', views.ResetUserAccountPasswordView.as_view(), name='reset_user_password'),
    path('api-token-auth/', auth_views.obtain_auth_token),
]

urlpatterns += router.urls
