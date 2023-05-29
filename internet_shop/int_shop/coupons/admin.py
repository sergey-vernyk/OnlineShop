from django.contrib import admin
from common.utils import ValidDiscountsListFilter
from .models import Coupon, Category


class ValidCouponListFilter(ValidDiscountsListFilter):
    """
    Фильтр по валидности купона
    """


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Купоны
    """
    list_display = ['code', 'category', 'valid_from', 'valid_to', 'is_valid', 'discount']
    list_filter = [ValidCouponListFilter, 'category']

    @admin.display(description='Valid status')
    def is_valid(self, instance):
        return 'Valid' if instance.is_valid else 'Invalid'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Категории купонов
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
