from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, authentication, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from account.models import Profile
from common.moduls_init import redis
from . import serializers
from .schemas import CouponActionsSchema
from ..models import Coupon, Category


class CouponViewSet(viewsets.ModelViewSet):
    """
    API views for obtaining, create, update and delete coupon
    """
    serializer_class = serializers.CouponSerializer
    queryset = Coupon.objects.select_related('category').prefetch_related('profile_coupons')
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [authentication.BasicAuthentication, authentication.TokenAuthentication]

    @action(methods=['POST'],
            detail=False,
            url_path='(?P<act>[a-zA-Z-_]+)?/(?P<coupon_pk>[0-9]+)?',
            url_name='apply_cancel_coupon',
            name='Apply or Cancel Coupon',
            schema=CouponActionsSchema())
    def apply_cancel_coupon(self, request, act: str, coupon_pk: int):
        """
        Action provides an opportunity to apply coupon or to cancel applied coupon to cart
        """
        coupon = get_object_or_404(Coupon, pk=coupon_pk)
        if not coupon.is_valid:
            raise ValidationError('Coupon is not valid', code='invalid_code')

        session = request.session
        profile = Profile.objects.get(user=request.user)
        if 'cart' in session and session['cart'] or redis.hget('session_cart', f'user_id:{request.user.pk}'):
            if act == 'apply':
                session.update({'coupon_id': int(coupon_pk)}) if request.headers.get(
                    'User-Agent') != 'coreapi' else redis.hset('coupon_id', f'user_id:{request.user.pk}', coupon_pk)
                profile.coupons.add(coupon)
            elif act == 'cancel':
                if request.headers.get('User-Agent') == 'coreapi':
                    redis.hdel('coupon_id', f'user_id:{request.user.pk}')
                else:
                    del session['coupon_id']

            session.save()
            return Response({'success': f"Coupon with code '{coupon.code}' has been successfully"
                                        f' {act + "ed" if act == "cancel" else act[:-1] + "ied"}'})
        else:
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_200_OK)


class CouponCategoryViewSet(viewsets.ModelViewSet):
    """
    API view for obtaining, create, update and delete coupon category
    """
    serializer_class = serializers.CouponCategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [authentication.BasicAuthentication, authentication.TokenAuthentication]
