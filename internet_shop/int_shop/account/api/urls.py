from django.conf import settings
from django.urls import path, re_path
from drf_yasg.utils import swagger_auto_schema
from rest_framework import routers
from rest_framework.authtoken import views as auth_views
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import get_schema_view, SchemaGenerator

from . import views

# generate schema view for the app
coreapi_schema_view = get_schema_view(title='Account API',
                                      url=f'/api/{settings.REST_FRAMEWORK["DEFAULT_VERSION"]}/account/',
                                      urlconf='account.api.urls',
                                      generator_class=SchemaGenerator,
                                      renderer_classes=[CoreJSONRenderer],
                                      description='API for account profile')

router = routers.DefaultRouter()
router.register(r'profile', views.AccountViewSet, basename='profile')

decorated_api_token_auth = swagger_auto_schema(
    method='post',
    operation_summary='Generate api token for user with passed `username` and `password`'
)(auth_views.obtain_auth_token)

app_name = 'account_api'

urlpatterns = [
    path('check_user_auth/', views.check_user_is_authenticate, name='check_user_auth'),
    re_path(r'^upload/(?P<photo_name>[^/]+)/?$', views.PhotoUploadView.as_view(), name='upload_photo'),
    path('reset_password/', views.ResetUserAccountPasswordView.as_view(), name='reset_user_password'),
    path('api-token-auth/', decorated_api_token_auth, name='get_api_token'),
    path('schema', coreapi_schema_view, name='coreapi_schema'),
]

urlpatterns += router.urls
