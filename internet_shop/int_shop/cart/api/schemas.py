import coreapi
import coreschema
from rest_framework.schemas import ManualSchema

add_or_update_cart_schema = ManualSchema(fields=[
    coreapi.Field(
        name='product_id',
        required=True,
        location='path',
        schema=coreschema.Number(description='Product identifier, which will be add to the cart'),
        type='integer'
    ),
    coreapi.Field(
        name='quantity',
        required=False,
        location='path',
        schema=coreschema.Number(description='Product quantity, which will be add to the cart'),
        type='integer'
    ),
])
