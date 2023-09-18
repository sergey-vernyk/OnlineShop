from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'present_cards', views.PresentCardViewSet, basename='present_card')
router.register(r'categories', views.PresentCardCategoryViewSet, basename='category')

app_name = 'present_cards_api'

urlpatterns = router.urls
