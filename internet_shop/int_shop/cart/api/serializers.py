from rest_framework import serializers


class CartSerializer(serializers.Serializer):
    """
    Serializer for displaying items in cart with their quantities, prices and product information
    """
    product_id = serializers.PrimaryKeyRelatedField(read_only=True, source='product.id')
    product_name = serializers.StringRelatedField(read_only=True, source='product.name')
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.00)
