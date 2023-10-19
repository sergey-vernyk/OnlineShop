from rest_framework import serializers

from coupons.models import Coupon, Category


class CouponSerializer(serializers.ModelSerializer):
    """
    Serializer for coupon
    """

    category = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Category.objects.all())
    category_name = serializers.StringRelatedField(read_only=True, source='category.name')
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        # `profile_coupons` field is reverse relation field in Profile model.
        # displays profile ids, where applied corresponds coupon
        fields = ('id', 'code', 'is_valid', 'valid_from', 'valid_to',
                  'discount', 'category', 'category_name',
                  'profile_coupons')
        read_only_fields = ('profile_coupons',)

    def remove_fields(self, fields: list):
        """
        Remove serializer's fields from response, which names in passed list
        """
        for field_name in fields:
            self.fields.pop(field_name)


class CouponCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for coupon category
    """
    coupons = serializers.StringRelatedField(read_only=True, many=True)

    class Meta:
        model = Category
        fields = '__all__'

    def remove_fields(self, fields: list):
        """
        Remove serializer's fields from response, which names in passed list
        """
        for field_name in fields:
            self.fields.pop(field_name)
