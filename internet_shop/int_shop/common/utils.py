from typing import Union

import phonenumbers
from django.contrib import admin
from phonenumbers import carrier


class ValidDiscountsListFilter(admin.SimpleListFilter):
    """
    Filter by validity discounts in admin site (list_filter)
    """
    title = 'Validation status'  # human-readable title which will be displayed in the right admin sidebar
    parameter_name = 'validation_status'  # parameter for the filter that will be used in the URL query.

    def lookups(self, request, model_admin) -> [tuple, tuple]:
        """
        The first element in each tuple is the coded value for the option that will
        appear in the URL query. The second element is the human-readable name for
        the option that will appear in the right sidebar.
        """
        return [
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via "self.value()"
        """
        if self.value() == 'valid':
            valid_ids = (x.id for x in queryset if x.is_valid)
            return queryset.filter(id__in=valid_ids)
        if self.value() == 'invalid':
            invalid_ids = (x.id for x in queryset if not x.is_valid)
            return queryset.filter(id__in=invalid_ids)


def check_phone_number(phone_number: str) -> Union[str, bool]:
    """
    Return phone number if it is correct, otherwise return False
    """
    phone_number_output = ''.join(num.strip('()') for num in phone_number.split())
    phone_number_parse = phonenumbers.parse(phone_number_output, 'UA')
    carrier_of_number = carrier.name_for_number(phone_number_parse, 'en')
    if phonenumbers.is_possible_number(phone_number_parse) and carrier_of_number in (
            'Kyivstar',
            'Vodafone',
            'lifecell'
    ):
        return phone_number_output
    else:
        return False
