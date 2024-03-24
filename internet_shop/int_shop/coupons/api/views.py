from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from drf_yasg.openapi import Parameter, Schema, TYPE_OBJECT
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models import Profile
from common.filters import ExtraSearchTerms
from common.moduls_init import redis
from .schemas import CouponActionsSchema
from .serializers import CouponSerializer, CouponCategorySerializer
from ..models import Coupon, Category


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all coupons',
                                                             manual_parameters=[Parameter(
                                                                 name='search',
                                                                 type='string',
                                                                 in_='query',
                                                                 description='Search by discount percent '
                                                                             '(int) or coupon validity (valid/invalid)'
                                                             )]))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create coupon'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Full update coupon with {id}'))
@method_decorator(name='partial_update',
                  decorator=swagger_auto_schema(operation_summary='Partial update coupon with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete coupon with {id}'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get coupon with {id}'))
class CouponViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` coupon.

    * get - obtain all coupons
    * post - create new coupon
    * get/{id} - retrieve coupon with `id`
    * patch/{id} - update one or several fields of coupon with `id`
    * put/{id} - update all fields of coupon with `id`
    * delete/{id} - delete coupon with `id`
    """
    serializer_class = CouponSerializer
    queryset = Coupon.objects.select_related('category').prefetch_related('profile_coupons')
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [ExtraSearchTerms]
    search_fields = ['discount', 'is_valid', 'code']
    remove_fields_list_for_get_request = ['valid_from', 'valid_to', 'profile_coupons']

    @swagger_auto_schema(method='post',
                         operation_summary='Apply coupon to cart or cancel applied coupon'
                                           ' in cart with {act} and {code}',
                         responses={'200': CouponSerializer(), '404': "Coupon with code '{code}' was not found"},
                         request_body=Schema(type=TYPE_OBJECT))
    @action(methods=['POST'],
            detail=False,
            url_path=r'(?P<act>(apply|cancel))?/(?P<code>[A-Za-z _0-9]+)?',
            url_name='apply_cancel_coupon',
            name='Apply or Cancel Coupon',
            schema=CouponActionsSchema(),
            permission_classes=[permissions.IsAuthenticated])
    def apply_or_cancel_coupon(self, request, act: str, code: str, version: str = 'v1'):
        """
        Action provides an opportunity to apply coupon to cart or to cancel applied coupon.
        To apply coupon need to send `apply` or `cancel` to cancel it, and send coupon `code` itself.
        """
        try:
            coupon = Coupon.objects.get(code=code.strip())
        except ObjectDoesNotExist:
            return Response({'error': f"Coupon with code '{code}' was not found"}, status=status.HTTP_404_NOT_FOUND)

        if not coupon.is_valid:
            return Response({'detail': 'Coupon is already invalid'})

        session = request.session
        profile = Profile.objects.get(user=request.user)
        if 'cart' in session and session['cart'] or \
                redis.hget('session_cart', f'user_id:{request.user.pk}') is not None:
            if act == 'apply':
                (
                    session.update({'coupon_id': coupon.pk})
                    if request.headers.get('User-Agent') != 'coreapi'
                    else redis.hset('coupon_id', f'user_id:{request.user.pk}', coupon.pk)
                )
                profile.coupons.add(coupon)
            elif act == 'cancel':
                if request.headers.get('User-Agent') == 'coreapi':
                    redis.hdel('coupon_id', f'user_id:{request.user.pk}')
                else:
                    del session['coupon_id']

            session.save()
            return Response({'success': f"Coupon with code '{coupon.code}' has been successfully"
                                        f' {act + "ed" if act == "cancel" else act[:-1] + "ied"}'},
                            status=status.HTTP_200_OK)
        return Response({'detail': 'Cart is empty'}, status=status.HTTP_200_OK)

    def filter_queryset(self, queryset, **kwargs):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self, **kwargs)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset, model=Coupon)
        page = self.paginate_queryset(queryset or self.queryset)
        if page:
            serializer = self.get_serializer(instance=page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=queryset or self.queryset)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all categories'))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create category'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Update category with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete category with {id}'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get category with {id}'))
class CouponCategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` category.

    * get - obtain all coupons categories
    * post - create new coupon category
    * get/{id} - retrieve coupon category with `id`
    * put/{id} - update all fields of coupon category with `id`
    * delete/{id} - delete coupon category with `id`
    """
    serializer_class = CouponCategorySerializer
    queryset = Category.objects.prefetch_related('coupons')
    permission_classes = [permissions.IsAdminUser]
    remove_fields_list_for_get_request = ['coupons']
    http_method_names = ['get', 'head', 'post', 'put', 'delete']

    def get_queryset(self):
        """
        Returns category instances depends on current language.
        """
        language = self.request.LANGUAGE_CODE
        queryset = Category.objects.prefetch_related('coupons').filter(
            translations__language_code=language)
        return queryset

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        if page:
            serializer = self.get_serializer(instance=page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=self.queryset)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
