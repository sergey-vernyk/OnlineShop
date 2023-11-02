from rest_framework import serializers
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
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

    def remove_fields(self, fields: list):
        """
        Remove serializer's fields from response, which names in passed list.
        """
        for field_name in fields:
            self.fields.pop(field_name)


class PresentCardCategorySerializer(TranslatableModelSerializer):
    """
    Serializer for coupon category.
    """
    translations = TranslatedFieldsField(shared_model=Category)
    present_cards = serializers.StringRelatedField(read_only=True, many=True)

    class Meta:
        model = Category
        fields = ('name', 'slug', 'present_cards', 'translations')

    def remove_fields(self, fields: list):
        """
        Remove serializer's fields from response, which names in passed list.
        """
        for field_name in fields:
            self.fields.pop(field_name)
