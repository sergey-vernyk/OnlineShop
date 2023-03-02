from django.contrib import admin

from coupons.models import Coupon, Category


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Купоны
    """
    list_display = ['code', 'valid_from', 'valid_to', 'discount', 'active']
    list_filter = ['active']
    list_editable = ['active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Категории купонов
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
