from django.contrib import admin


class ValidDiscountsListFilter(admin.SimpleListFilter):
    """
    Filter by validity discounts in admin site (list_filter)
    """
    title = 'Validation status'
    parameter_name = 'validation_status'

    def lookups(self, request, model_admin):
        return [
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'valid':
            valid_ids = (x.id for x in queryset if x.is_valid)
            return queryset.filter(id__in=valid_ids)
        if self.value() == 'invalid':
            invalid_ids = (x.id for x in queryset if not x.is_valid)
            return queryset.filter(id__in=invalid_ids)
