from rest_framework import serializers

from goods.models import Product, Category, Property, Manufacturer, PropertyCategory


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer with product information about names of category, manufacturer which product belongs to,
    and comments, that belongs to the product
    """
    category = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Category.objects.all())
    manufacturer = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Manufacturer.objects.all())
    comments = serializers.StringRelatedField(many=True, required=False)

    class Meta:
        model = Product
        exclude = ('star', 'description')

    def validate(self, attrs):
        """
        Additional validate both "price" and "promotional price" fields
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


class ProductsCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for products categories
    """

    class Meta:
        model = Category
        fields = '__all__'


class ProductPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for products properties
    """

    class Meta:
        model = Property
        fields = '__all__'


class ManufacturersSerializer(serializers.ModelSerializer):
    """
    Serializer for products manufacturers
    """

    class Meta:
        model = Manufacturer
        exclude = ('description',)
