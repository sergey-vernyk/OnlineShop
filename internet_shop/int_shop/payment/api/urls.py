from django.urls import path
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import SchemaGenerator, get_schema_view

from . import views

# generate schema view for the app
schema_view = get_schema_view(title='Payment API',
                              url='/api/payment/',
                              urlconf='payment.api.urls',
                              generator_class=SchemaGenerator,
                              renderer_classes=[CoreJSONRenderer],
                              authentication_classes=[TokenAuthentication, BasicAuthentication],
                              description='API for making online payment')
app_name = 'payment_api'

urlpatterns = [
    path('make_payment/', views.MakePaymentView.as_view(), name='make_payment'),
    path('schema', schema_view)
]
