from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, authentication, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from account.models import Profile
from present_cards.models import PresentCard, Category
from . import serializers


class PresentCardViewSet(viewsets.ModelViewSet):
    """
    API view for obtaining, create, update and delete present card
    """
    queryset = PresentCard.objects.all()
    serializer_class = serializers.PresentCardSerializer
    authentication_classes = [authentication.TokenAuthentication, authentication.BasicAuthentication]
    permission_classes = [permissions.IsAdminUser]

    @action(methods=['POST'],
            detail=False,
            url_path='(?P<act>[a-zA-Z-_]+)?/(?P<card_pk>[0-9]+)?',
            url_name='apply_cancel_present_card',
            name='Apply or Cancel Present Card')
    def apply_cancel_present_card(self, request, act: str, card_pk: int):
        """
        Action provides an opportunity to apply present card or to cancel applied present card to cart
        """
        present_card = get_object_or_404(PresentCard, pk=card_pk)
        if not present_card.is_valid:
            raise ValidationError('Present card is not valid', code='invalid_code')

        session = request.session
        profile = Profile.objects.get(user=request.user)
        if 'cart' in session and session['cart']:
            if act == 'apply':
                session.update({'present_card_id': card_pk})
                present_card.profile = profile
            elif act == 'cancel':
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
    API view for obtaining, create, update and delete coupon category
    """
    serializer_class = serializers.PresentCardCategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [authentication.BasicAuthentication, authentication.TokenAuthentication]
