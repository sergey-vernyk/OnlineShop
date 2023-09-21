"""int_shop URL Configurationgoods

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from common.utils import create_captcha_image

urlpatterns = [
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
    path('api/goods/', include('goods.api.urls')),
    path('api/account/', include('account.api.urls')),
    path('api/cart/', include('cart.api.urls')),
    path('api/coupons/', include('coupons.api.urls')),
    path('api/present_cards/', include('present_cards.api.urls')),
    path('api/orders/', include('orders.api.urls')),
]

if settings.DEBUG:  # save files will be happened to this path only in debug mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
