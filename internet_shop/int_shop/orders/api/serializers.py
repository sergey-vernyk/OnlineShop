from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from account.models import Profile
from common.moduls_init import redis
from common.utils import check_phone_number
from orders.models import Order, OrderItem, Delivery


class OrderItemsSerializer(serializers.ModelSerializer):
    """
    Serializer for items of order
    """

    product_id = serializers.IntegerField(read_only=True, source='product.id')
    product_name = serializers.StringRelatedField(read_only=True, source='product.name')

    class Meta:
        model = OrderItem
        fields = ('product_id', 'product_name', 'quantity', 'price')


class DeliverySerializer(serializers.ModelSerializer):
    """
    Serializer for order delivery
    """

    class Meta:
        model = Delivery
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for order
    """

    items = OrderItemsSerializer(many=True, read_only=True)
    delivery = DeliverySerializer(read_only=False)

    class Meta:
        model = Order
        fields = ('id', 'first_name', 'last_name', 'email', 'address',
                  'phone', 'comment', 'pay_method', 'call_confirm',
                  'is_paid', 'is_done', 'stripe_id', 'present_card', 'coupon',
                  'profile', 'created', 'updated', 'items', 'delivery')
        read_only_fields = ('stripe_id', 'present_card', 'coupon',
                            'profile', 'created', 'updated', 'items',
                            'is_paid', 'is_done')

    def remove_fields(self, fields: list):
        """
        Remove serializer's fields from response, which names in passed list
        """
        for field_name in fields:
            self.fields.pop(field_name)

    def validate(self, attrs):
        """
        Additional validation of delivery, phone, address, delivery method and delivery date while creating order
        """
        delivery_method = None

        delivery_info = attrs.get('delivery')
        phone = attrs.get('phone')
        address = attrs.get('address')
        if delivery_info:
            delivery_method = delivery_info.get('method')
            office_number = delivery_info.get('office_number')
            delivery_date = delivery_info.get('delivery_date')

            now = timezone.now().date()
            if delivery_date and delivery_date < now:
                raise ValidationError({'delivery_date': 'Delivery date must be greater then today'},
                                      code='invalid_date')

            if (delivery_method == 'Post office' and not office_number) or (
                    delivery_method != 'Post office' and office_number):
                raise ValidationError("You must provide 'method' as 'Post office' if 'office_number' is provided or "
                                      "provide 'office_number' if provided 'method' is 'Post office'",
                                      code='missing_parameter')

        if phone and not check_phone_number(phone):
            raise ValidationError({'phone': 'Invalid phone number'}, code='invalid_phone')

        if address and not delivery_method == 'Apartment':
            raise ValidationError("You must enter delivery method as 'Apartment', when address was provided",
                                  code='missing_parameter')
        if delivery_method == 'Apartment' and not address:
            raise ValidationError("You must enter address, when delivery method is 'Apartment'",
                                  code='missing_parameter')

        return attrs

    def create(self, validated_data):
        """
        Create order with delivery, discounts and profile
        """
        delivery_info = validated_data.pop('delivery')
        # get data from the serializer's context
        cart_items = self.context['cart_items']
        current_user_pk = self.context['request'].user.pk

        if self.context['request'].headers.get('User-Agent') == 'coreapi':
            coupon = redis.hget('coupon_id', f'user_id:{current_user_pk}')
            present_card = redis.hget('present_card_id', f'user_id:{current_user_pk}')
        else:
            coupon = self.context['request'].session.get('coupon_id')
            present_card = self.context['request'].session.get('present_card')

        profile = Profile.objects.get(user_id=current_user_pk)

        # delete cart content, coupon_id or present_card_id if they were existed
        if self.context['request'].headers.get('User-Agent') == 'coreapi':
            redis.hdel('session_cart', f'user_id:{current_user_pk}')
            redis.hdel('coupon_id', f'user_id:{current_user_pk}')
            redis.hdel('present_card_id', f'user_id:{current_user_pk}')
        else:
            self.context['request'].session['cart'].clear()

        delivery = Delivery.objects.create(**delivery_info)
        # create order and assign to it profile, delivery, coupon or present card
        order = Order(**validated_data)
        order.profile = profile
        order.delivery = delivery
        order.coupon_id = coupon
        order.present_card_id = present_card
        order.save()
        # create order items from items in cart
        for item in cart_items:
            OrderItem.objects.create(order=order,
                                     product=item['product'],
                                     price=item['price'],
                                     quantity=item['quantity'])

        if self.context['request'].headers.get('User-Agent') == 'coreapi':
            redis.hset('order_id', f'user_id:{current_user_pk}', order.pk)
        else:
            self.context['request'].session['order_id'] = order.pk

        return order

    def update(self, instance, validated_data):
        """
        Update order info
        """
        delivery_info = validated_data.pop('delivery', None)

        if delivery_info:
            delivery_instance = Delivery.objects.get(pk=instance.delivery_id)
            for field, value in delivery_info.items():
                setattr(delivery_instance, field, value)
            delivery_instance.save(update_fields=[*delivery_info.keys()])

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=[*validated_data.keys()])

        return instance
