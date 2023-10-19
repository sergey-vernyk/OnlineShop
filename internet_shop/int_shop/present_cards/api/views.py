from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from drf_yasg.openapi import Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models import Profile
from common.moduls_init import redis
from common.filters import ExtraSearchTerms
from present_cards.models import PresentCard, Category
from . import serializers
from .schemas import PresentCardActionsSchema
from .serializers import PresentCardSerializer


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all present cards',
                                                             manual_parameters=[Parameter(
                                                                 name='search',
                                                                 type='string',
                                                                 in_='query',
                                                                 description='Search by discount amount (int) '
                                                                             'or present card validity (valid/invalid)'
                                                             )]))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create present card'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Update present card with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete present card with {id}'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get present card with {id}'))
class PresentCardViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` present card.

    * get - obtain all present cards
    * post - create new present card
    * get/{id} - retrieve present card with `id`
    * patch/{id} - update one or several fields of present card with `id`
    * put/{id} - update all fields of present card with `id`
    * delete/{id} - delete present card with `id`
    """
    queryset = PresentCard.objects.all()
    serializer_class = serializers.PresentCardSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [ExtraSearchTerms]
    search_fields = ['amount', 'is_valid']
    remove_fields_list_for_get_request = ['profile', 'valid_from', 'valid_to', 'from_name',
                                          'from_email', 'to_name', 'to_email', 'message']

    @swagger_auto_schema(method='post', operation_summary='Apply present card to cart or cancel applied present card'
                                                          ' in cart with {act} and {code}',
                         responses={'200': PresentCardSerializer(), '404': "Coupon with code '{code}' was not found"})
    @action(methods=['POST'],
            detail=False,
            url_path=r'(?P<act>(apply|cancel))?/(?P<code>[A-Za-z _0-9]+)?',
            url_name='apply_or_cancel_present_card',
            name='Apply or Cancel Present Card',
            schema=PresentCardActionsSchema(),
            permission_classes=[permissions.IsAuthenticated])
    def apply_or_cancel_present_card(self, request, act: str, code: str, version: str = 'v1'):
        """
        Action provides an opportunity to apply present card or to cancel applied present card to cart.
        To apply present card need to send `apply` or `cancel` to cancel it, and send `code` itself.
        """
        try:
            present_card = PresentCard.objects.get(code=code.strip())
        except ObjectDoesNotExist:
            return Response({'error': f"Present card with code '{code}' was not found"},
                            status=status.HTTP_404_NOT_FOUND)

        session = request.session
        profile = Profile.objects.get(user=request.user)
        if ('cart' in session and session['cart']) or redis.hget('session_cart', f'user_id:{request.user.pk}'):
            if act == 'apply':
                session.update({'present_card_id': present_card.pk}) if request.headers.get(
                    'User-Agent') != 'coreapi' else redis.hset(
                    'present_card_id', f'user_id:{request.user.pk}', present_card.pk)
                present_card.profile = profile
            elif act == 'cancel':
                if request.headers.get('User-Agent') == 'coreapi':
                    redis.hdel('present_card_id', f'user_id:{request.user.pk}')
                else:
                    del session['present_card_id']

                present_card.profile = None

            session.save()
            present_card.save(update_fields=['profile'])
            return Response({'success': f"Present card with code '{present_card.code}' has been successfully"
                                        f' {act + "ed" if act == "cancel" else act[:-1] + "ied"}'})
        else:
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_200_OK)

    def filter_queryset(self, queryset, **kwargs):
        """
        Given a queryset, filter it with whichever filter backend is in use.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self, **kwargs)
        return queryset

    def list(self, request, *args, **kwargs):
        # queryset with taking into account search term if any
        queryset = self.filter_queryset(self.queryset, model=PresentCard)
        page = self.paginate_queryset(queryset or self.queryset)
        if page:
            serializer = self.get_serializer(instance=page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=queryset or self.queryset, many=True)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(name='list', decorator=swagger_auto_schema(operation_summary='Get all categories'))
@method_decorator(name='create', decorator=swagger_auto_schema(operation_summary='Create category'))
@method_decorator(name='update', decorator=swagger_auto_schema(operation_summary='Update category with {id}'))
@method_decorator(name='destroy', decorator=swagger_auto_schema(operation_summary='Delete category with {id}'))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(operation_summary='Get category with {id}'))
class PresentCardCategoryViewSet(viewsets.ModelViewSet):
    """
   Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` category.

    * get - obtain all present cards categories
    * post - create new present card category
    * get/{id} - retrieve present card category with `id`
    * put/{id} - update all fields of present card category with id
    * delete/{id} - delete present card category with id
    """
    serializer_class = serializers.PresentCardCategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAdminUser]
    remove_fields_list_for_get_request = ['present_cards']
    http_method_names = ['get', 'head', 'post', 'put', 'delete']

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.queryset)
        if page:
            serializer = self.get_serializer(instance=page, many=True)
            serializer.child.remove_fields(self.remove_fields_list_for_get_request)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(instance=self.queryset)
        serializer.child.remove_fields(self.remove_fields_list_for_get_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
