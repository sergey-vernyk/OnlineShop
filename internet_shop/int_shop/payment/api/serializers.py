from rest_framework import serializers

from goods.models import Product


class ProductNameField(serializers.RelatedField):
    """
    Custom field for displaying product name, when received product id
    """

    def to_internal_value(self, data):
        name = self.get_queryset().get(pk=data).name
        return f'({data}){name}'

    def to_representation(self, value):
        return value

    def get_queryset(self):
        return Product.available_objects.all()


class PaymentSerializer(serializers.Serializer):
    """
    Serializer for displaying info with products, which customer going to buy,
    its quantities, and possible discounts.
    """

    product_id = ProductNameField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
