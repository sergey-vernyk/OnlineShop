from django.urls import path
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view, SchemaGenerator

from . import views

# generate schema view for the app
schema_view = get_schema_view(title='Present cards API',
                              url='/api/present_cards/',
                              urlconf='present_cards.api.urls',
                              generator_class=SchemaGenerator,
                              renderer_classes=[CoreJSONRenderer],
                              description='API for present_card, which can be applied to cart')

router = DefaultRouter()
router.register(r'present_card', views.PresentCardViewSet, basename='present_card')
router.register(r'category', views.PresentCardCategoryViewSet, basename='category')

app_name = 'present_cards_api'

urlpatterns = [
    path('schema', schema_view)
]

urlpatterns += router.urls
