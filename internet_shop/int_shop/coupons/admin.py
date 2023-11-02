from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from common.utils import ValidDiscountsListFilter
from .models import Coupon, Category


class ValidCouponListFilter(ValidDiscountsListFilter):
    """
    Filter for coupon validity.
    """


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Coupons
    """
    list_display = ['pk', 'code', 'category', 'valid_from', 'valid_to', 'is_valid', 'discount']
    list_filter = [ValidCouponListFilter, 'category']

    @admin.display(description=_('Valid status'))
    def is_valid(self, instance):
        return _('Valid') if instance.is_valid else _('Invalid')


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    """
    Coupons categories
    """
    list_display = ['name', 'slug']

    def get_prepopulated_fields(self, request, obj=None) -> dict[str, tuple[str]]:
        return {'slug': ('name',)}
