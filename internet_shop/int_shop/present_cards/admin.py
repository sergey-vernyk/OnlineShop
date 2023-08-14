from django.contrib import admin
from common.utils import ValidDiscountsListFilter
from present_cards.models import PresentCard, Category


class ValidCardListFilter(ValidDiscountsListFilter):
    """
    Filter by validity present card
    """


@admin.register(PresentCard)
class PresentCardAdmin(admin.ModelAdmin):
    """
    Info about present card in admin panel
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

    list_display = ['code', 'amount', 'valid_from', 'valid_to', 'is_valid']
    list_filter = [ValidCardListFilter]

    @admin.display(description='Valid status')
    def is_valid(self, instance):
        return 'Valid' if instance.is_valid else 'Invalid'


@admin.register(Category)
class PresentCardCategoryAdmin(admin.ModelAdmin):
    """
    Info about present card category in admin panel
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
