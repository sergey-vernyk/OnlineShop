import operator
from functools import reduce

from django.db import models
from rest_framework import filters
from rest_framework.compat import distinct


class ExtraSearchTerms(filters.SearchFilter):
    """
    Add extra search terms, which are not a model's fields. E.g. it can be model `@property`
    """

    def filter_queryset(self, request, queryset, view, **kwargs) -> list:
        """
        Override the method for add searching not only by model's fields, but also by model `@property`.
        """
        # make copy to prevent removing items from original `search_fields` list of a class
        search_fields = self.get_search_fields(view, request)[:]
        search_terms = self.get_search_terms(request)

        if not search_fields or not search_terms:
            return queryset

        if 'valid' in search_terms:
            return [card for card in kwargs['model'].objects.all() if card.is_valid]
        elif 'invalid' in search_terms:
            return [card for card in kwargs['model'].objects.all() if not card.is_valid]
        else:
            search_fields.remove('is_valid')  # remove this from search terms since `is_valid` it is not a model field

        orm_lookups = [
            self.construct_search(str(search_field))
            for search_field in search_fields
        ]

        base = queryset
        conditions = []
        for search_term in search_terms:
            queries = [
                models.Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            conditions.append(reduce(operator.or_, queries))
        queryset = queryset.filter(reduce(operator.and_, conditions))

        if self.must_call_distinct(queryset, search_fields):
            # Filtering against a many-to-many field requires us to
            # call queryset.distinct() in order to avoid duplicate items
            # in the resulting queryset.
            # We try to avoid this if possible, for performance reasons.
            queryset = distinct(queryset, base)
        return queryset
