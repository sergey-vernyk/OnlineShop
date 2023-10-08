from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models import Profile
from common.moduls_init import redis
from . import serializers
from .schemas import CouponActionsSchema
from ..models import Coupon, Category


class CouponViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

    * get - obtain all coupons
    * post - create new coupon
    * get/{id} - retrieve coupon with `id`
    * patch/{id} - update one or several fields of coupon with `id`
    * put/{id} - update all fields of coupon with id
    * delete/{id} - delete coupon with `id`
    """
    serializer_class = serializers.CouponSerializer
    queryset = Coupon.objects.select_related('category').prefetch_related('profile_coupons')
    permission_classes = [permissions.IsAdminUser]

    @action(methods=['POST'],
            detail=False,
            url_path=r'(?P<act>(apply|cancel))?/(?P<code>[A-Za-z _0-9]+)?',
            url_name='apply_cancel_coupon',
            name='Apply or Cancel Coupon',
            schema=CouponActionsSchema(),
            permission_classes=[permissions.IsAuthenticated])
    def apply_or_cancel_coupon(self, request, act: str, code: str):
        """
        Action provides an opportunity to apply coupon to cart or to cancel applied coupon.
        To apply coupon need to send `apply` or `cancel` to cancel it, and send coupon `code` itself
        """
        try:
            coupon = Coupon.objects.get(code=code.strip())
        except ObjectDoesNotExist:
            return Response({'error': f"Coupon with code '{code}' is not found"}, status=status.HTTP_404_NOT_FOUND)

        session = request.session
        profile = Profile.objects.get(user=request.user)
        if 'cart' in session and session['cart'] or redis.hget('session_cart', f'user_id:{request.user.pk}'):
            if act == 'apply':
                session.update({'coupon_id': coupon.pk}) if request.headers.get(
                    'User-Agent') != 'coreapi' else redis.hset('coupon_id', f'user_id:{request.user.pk}', coupon.pk)
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
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

    * get - obtain all coupons categories
    * post - create new coupon category
    * get/{id} - retrieve coupon category with `id`
    * put/{id} - update all fields of coupon category with id
    * delete/{id} - delete coupon category with id
    """
    serializer_class = serializers.CouponCategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAdminUser]
