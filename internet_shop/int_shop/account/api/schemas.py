from copy import deepcopy

from rest_framework.schemas import AutoSchema


class FavoriteActionsSchema(AutoSchema):
    """
    Schema with particular fields inside
    """

    def get_link(self, path, method, base_url):
        link = super().get_link(path, method, base_url)
        fields = list(deepcopy(link.fields))
        # leave only 2 fields for this action
        for field in link.fields:
            if field.name not in ('product_pk', 'act'):
                fields.remove(field)

        link._fields = tuple(fields)  # replace field instances in the link
        return link
