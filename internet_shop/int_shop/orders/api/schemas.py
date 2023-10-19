from copy import deepcopy

import coreapi
import coreschema
from rest_framework.schemas import ManualSchema, AutoSchema

# schema for delivery action
get_deliveries_by_user_schema = ManualSchema(fields=[
    coreapi.Field(
        name='username',
        required=True,
        type='string',
        location='path',
        schema=coreschema.String(description='Field for enter username, by which will return all own deliveries')
    )
])

# schema for order action
get_orders_by_user_schema = ManualSchema(fields=[
    coreapi.Field(
        name='username',
        required=True,
        type='string',
        location='path',
        schema=coreschema.String(description='Field for enter username, by which will return all own orders')
    )
])


class OrderSchema(AutoSchema):
    """
    Schema displays only particular fields
    """

    def get_link(self, path, method, base_url):
        link = super().get_link(path, method, base_url)
        if method in ('POST', 'PUT', 'PATCH'):
            fields = list(deepcopy(link.fields))
            for field in link.fields:
                if field.name in ('is_paid', 'is_done', 'stripe_id', 'present_card', 'coupon', 'profile'):
                    fields.remove(field)
            link._fields = tuple(fields)
        return link
