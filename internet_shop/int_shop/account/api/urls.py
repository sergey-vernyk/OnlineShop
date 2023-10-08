from django.urls import path, re_path
from rest_framework import routers
from rest_framework.authtoken import views as auth_views
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import get_schema_view, SchemaGenerator

from . import views

# generate schema view for the app
coreapi_schema_view = get_schema_view(title='Account API',
                                      url='/api/account/',
                                      urlconf='account.api.urls',
                                      generator_class=SchemaGenerator,
                                      renderer_classes=[CoreJSONRenderer],
                                      description='API for account profile')

router = routers.DefaultRouter()
router.register(r'profile', views.AccountViewSet, basename='profile')

app_name = 'account_api'

urlpatterns = [
    path('check_user_auth/', views.check_user_is_authenticate, name='check_user_auth'),
    re_path(r'^upload/(?P<photo_name>[^/]+)/?$', views.PhotoUploadView.as_view(), name='upload_photo'),
    path('reset_password/', views.ResetUserAccountPasswordView.as_view(), name='reset_user_password'),
    path('api-token-auth/', auth_views.obtain_auth_token),
    path('schema', coreapi_schema_view, name='coreapi_schema'),
]

urlpatterns += router.urls
