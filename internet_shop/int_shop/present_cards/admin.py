from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from common.utils import ValidDiscountsListFilter
from present_cards.models import PresentCard, Category


class ValidCardListFilter(ValidDiscountsListFilter):
    """
    Filter by validity present card.
    """


@admin.register(PresentCard)
class PresentCardAdmin(admin.ModelAdmin):
    """
    Info about present card in admin panel.
    """
    fieldsets = (
        ('General info', {
            'fields': ('code', 'valid_from', 'valid_to')
        }),
        ('Contacts', {
            'fields': ('from_name', 'from_email', 'to_name', 'to_email')
        }),
        ('Additional info', {
            'fields': ('category', 'message', 'amount', 'profile')
        })
    )

    list_display = ['id', 'code', 'amount', 'valid_from', 'valid_to', 'is_valid']
    list_filter = [ValidCardListFilter]

    @admin.display(description=_('Valid status'))
    def is_valid(self, instance):
        return _('Valid') if instance.is_valid else _('Invalid')


@admin.register(Category)
class PresentCardCategoryAdmin(TranslatableAdmin):
    """
    Info about present card category.
    """
    list_display = ['name', 'slug']

    def get_prepopulated_fields(self, request, obj=None) -> dict[str, tuple[str]]:
        return {'slug': ('name',)}
