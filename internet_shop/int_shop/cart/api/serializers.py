from rest_framework import serializers

from goods.models import Product


class ProductNameField(serializers.Field):
    """
    Field for displaying product name
    """

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class CartSerializer(serializers.Serializer):
    """
    Serializer for displaying items in cart with their quantities, prices and product information
    """
    product_id = serializers.PrimaryKeyRelatedField(read_only=False,
                                                    source='product.id',
                                                    queryset=Product.available_objects.all())
    product_name = ProductNameField(read_only=False, source='product.name')
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.00)
