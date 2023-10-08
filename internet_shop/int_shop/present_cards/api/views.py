from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from account.models import Profile
from common.moduls_init import redis
from present_cards.models import PresentCard, Category
from . import serializers
from .schemas import PresentCardActionsSchema


class PresentCardViewSet(viewsets.ModelViewSet):
    """
    Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

    * get - obtain all present cards
    * post - create new present card
    * get/{id} - retrieve present card with `id`
    * patch/{id} - update one or several fields of present card with `id`
    * put/{id} - update all fields of present card with id
    * delete/{id} - delete present card with id
    """
    queryset = PresentCard.objects.all()
    serializer_class = serializers.PresentCardSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(methods=['POST'],
            detail=False,
            url_path=r'(?P<act>(apply|cancel))?/(?P<code>[A-Za-z 0-9]+)?',
            url_name='apply_cancel_present_card',
            name='Apply or Cancel Present Card',
            schema=PresentCardActionsSchema(),
            permission_classes=[permissions.IsAuthenticated])
    def apply_cancel_present_card(self, request, act: str, code: str):
        """
        Action provides an opportunity to apply present card or to cancel applied present card to cart.
        To apply present card need to send `apply` or `cancel` to cancel it, and send `code` itself
        """
        present_card = get_object_or_404(PresentCard, code=code.strip())
        if not present_card.is_valid:
            raise ValidationError('Present card is not valid', code='invalid_code')

        session = request.session
        profile = Profile.objects.get(user=request.user)
        if ('cart' in session and session['cart']) or redis.hget('session_cart', f'user_id:{request.user.pk}'):
            if act == 'apply':
                session.update({'present_card_id': present_card.pk}) if request.headers.get(
                    'User-Agent') != 'coreapi' else redis.hset('present_card_id', f'user_id:{request.user.pk}', card_pk)
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


class PresentCardCategoryViewSet(viewsets.ModelViewSet):
    """
   Viewset that provides `retrieve`, `create`, `delete`, `list` and `update` actions.

    * get - obtain all present cards categories
    * post - create new present card category
    * get/{id} - retrieve present card category with `id`
    * put/{id} - update all fields of present card category with id
    * delete/{id} - delete present card category with id
    """
    serializer_class = serializers.PresentCardCategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAdminUser]
