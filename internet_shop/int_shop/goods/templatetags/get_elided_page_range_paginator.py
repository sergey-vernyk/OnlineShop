from django import template

register = template.Library()


@register.simple_tag
def get_elided_page_range_paginator(paginator_obj, number, on_each_side, on_ends):
    """
    Tag, which returns a 1-based list of page numbers,
    but may add an ellipsis to either or both sides of the current page number when number of pages is large
    """
    page_range = paginator_obj.get_elided_page_range(number, on_each_side=on_each_side, on_ends=on_ends)
    return page_range
