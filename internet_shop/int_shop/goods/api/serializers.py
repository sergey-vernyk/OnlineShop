from rest_framework import serializers

from goods.models import Product, Category, Property


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for obtaining product information with names of category and manufacturer belongs it
    """
    category = serializers.PrimaryKeyRelatedField(read_only=True, source='category.name')
    manufacturer = serializers.PrimaryKeyRelatedField(read_only=True, source='manufacturer.name')

    class Meta:
        model = Product
        exclude = ('star', 'description')


class ProductsCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for obtaining all products categories
    """

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class ProductPropertiesSerializer(serializers.ModelSerializer):
    """
    Serializer for obtaining all products properties
    """
    product = serializers.PrimaryKeyRelatedField(read_only=True, source='product.name')

    class Meta:
        model = Property
        fields = '__all__'
