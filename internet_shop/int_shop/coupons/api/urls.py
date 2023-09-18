from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'coupons', views.CouponViewSet, basename='coupon')
router.register(r'categories', views.CouponCategoryViewSet, basename='category')

app_name = 'coupons_api'

urlpatterns = router.urls
