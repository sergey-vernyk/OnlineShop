from django.contrib import admin

from present_cards.models import PresentCard, Category


@admin.register(PresentCard)
class PresentCardAdmin(admin.ModelAdmin):
    fieldsets = (
        ('General info', {
            'fields': ('code', 'valid_from', 'valid_to')
        }),
        ('Contacts', {
            'fields': ('from_name', 'from_email', 'to_name', 'to_email')
        }),
        ('Additional info', {
            'fields': ('category', 'message', 'amount', 'active')
        })
    )


@admin.register(Category)
class PresentCardAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}