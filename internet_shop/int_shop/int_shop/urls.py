from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

from common.utils import create_captcha_image
from .settings import env


class HttpsSchemaGenerator(OpenAPISchemaGenerator):
    """
    API schema generator for using API Swagger only over HTTPS protocol.
    """

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ['https']
        return schema


swagger_schema_view = get_schema_view(
    openapi.Info(
        title="OnlineShop API",
        default_version='v1',
        description='API allows interact with products, accounts, coupons, present cards, '
                    'cart, orders, payment',
        contact=openapi.Contact(email=env('ADMIN_USERS').split(':')[1]),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    generator_class=HttpsSchemaGenerator,
    validators=['ssv'],
    permission_classes=[AllowAny],
)
# view sets a user’s language preference and redirects to a given URL
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('goods.urls')),
    path('account/', include('account.urls')),
    path('orders/', include('orders.urls')),
    path('cart/', include('cart.urls')),
    path('coupons/', include('coupons.urls')),
    path('present_cards/', include('present_cards.urls')),
    path('payment/', include('payment.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('delivery/', TemplateView.as_view(template_name='./delivery.html'), name='delivery_services'),
    path('contacts/', TemplateView.as_view(template_name='./contacts.html'), name='contacts'),
    path('ajax/update_captcha/', create_captcha_image, name='update_captcha'),
    path('jsi18n/cart/', JavaScriptCatalog.as_view(packages=['cart']), name='javascript-catalog'),
    path('jsi18n/goods/', JavaScriptCatalog.as_view(packages=['goods']), name='javascript-catalog'),
    re_path(r'^api/(?P<version>(v1|v2))/goods/', include('goods.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/account/', include('account.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/cart/', include('cart.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/coupons/', include('coupons.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/present_cards/', include('present_cards.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/orders/', include('orders.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/payment/', include('payment.api.urls')),
    re_path(r'^api/(?P<version>(v1|v2))/swagger(?P<format>.(json|yaml))$',
            swagger_schema_view.without_ui(cache_timeout=0),
            name='schema-json_or_yaml'),
    re_path(r'^api/(?P<version>(v1|v2))/swagger/$',
            swagger_schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'),
    re_path(r'^api/(?P<version>(v1|v2))/redoc/$',
            swagger_schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc'),

    prefix_default_language=False
)

if settings.DEBUG:  # save files will be happened to this path only in debug mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
