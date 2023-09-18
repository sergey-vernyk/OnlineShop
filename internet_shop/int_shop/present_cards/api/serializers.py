from rest_framework import serializers

from present_cards.models import PresentCard, Category


class PresentCardSerializer(serializers.ModelSerializer):
    """
    Serializer for present card
    """

    category = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Category.objects.all())
    category_name = serializers.StringRelatedField(read_only=True, source='present_card.name')
    is_valid = serializers.BooleanField(read_only=True)
    profile = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PresentCard
        fields = '__all__'


class PresentCardCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for coupon category
    """
    present_cards = serializers.StringRelatedField(read_only=True, many=True)

    class Meta:
        model = Category
        fields = '__all__'
