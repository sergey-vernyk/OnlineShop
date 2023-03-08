from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from account.models import Profile
from present_cards.forms import PresentCardApplyForm
from present_cards.models import PresentCard


def apply_present_card(request):
    """
    Применение подарочной карты со страницы корзины
    и добавление ее в профиль пользователя
    """
    now = timezone.now()
    if request.method == 'POST':
        coupon_form = PresentCardApplyForm(request.POST)
        if coupon_form.is_valid():
            code = coupon_form.cleaned_data.get('code')
            try:
                present_card = PresentCard.objects.get(code__iexact=code,
                                                       valid_from__lte=now,
                                                       valid_to__gte=now,
                                                       active=True)
            except ObjectDoesNotExist:
                request.session['present_card_id'] = None
            else:
                request.session['present_card_id'] = present_card.pk
                Profile.objects.get(user=request.user).profile_cards.add(present_card)

    return redirect('cart:cart_detail')


def cancel_present_card(request):
    """
    Отмена применения подарочной карты к корзине,
    удаление ее из сессии и из пользовательского профиля
    """
    Profile.objects.get(user=request.user).profile_cards.update(profile_id=None)

    del request.session['present_card_id']
    request.session.modified = True

    return redirect('cart:cart_detail')
