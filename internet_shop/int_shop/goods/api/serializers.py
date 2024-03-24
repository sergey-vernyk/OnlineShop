from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers

from goods.models import Product, Category, Property, Manufacturer


class ProductPropertySerializer(TranslatableModelSerializer):
    """
    Serializer for products properties.
    """

    translations = TranslatedFieldsField(shared_model=Property)
    product_name = serializers.StringRelatedField(read_only=True, source='product.name')
    product = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Product.available_objects.all())

    class Meta:
        model = Property
        fields = ('translations', 'numeric_value', 'category_property', 'product_name', 'product')


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer with product information about names of category, manufacturer which product belongs to,
    and comments, that belongs to the product.
    """
    category = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Category.objects.all())
    manufacturer = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Manufacturer.objects.all())
    comments = serializers.StringRelatedField(many=True, required=False)
    properties = ProductPropertySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        exclude = ('star', 'description')

    def validate(self, attrs):
        """
        Additional validate both `price` and `promotional price` fields.
        """
        price = attrs.get('price')
        promotional_price = attrs.get('promotional_price')

        if price and price < 0:
            raise serializers.ValidationError({'price': 'Price must be greater than zero'})

        if promotional_price and promotional_price < 0:
            raise serializers.ValidationError({'promotional_price': 'Price must be greater than zero'})
        elif promotional_price and promotional_price > price:
            raise serializers.ValidationError(
                {'promotional_price': 'Promotional price must not be greater than default price'}
            )
        return attrs

    def remove_fields(self, fields: list):
        """
        Remove serializer's fields from response, which names are in passed list.
        """
        for field_name in fields:
            self.fields.pop(field_name)


class ProductCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for products categories
    """

    class Meta:
        model = Category
        fields = '__all__'


class ManufacturerSerializer(serializers.ModelSerializer):
    """
    Serializer for products manufacturers
    """

    class Meta:
        model = Manufacturer
        fields = '__all__'
