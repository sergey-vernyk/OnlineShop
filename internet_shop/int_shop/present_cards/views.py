from account.models import Profile
from present_cards.forms import PresentCardApplyForm
from present_cards.models import PresentCard
from common.decorators import ajax_required
from django.views.decorators.http import require_POST
from django.http.response import JsonResponse
from common.decorators import auth_profile_required


@auth_profile_required
@ajax_required
@require_POST
def apply_present_card(request):
    """
    Применение подарочной карты со страницы корзины
    и добавление ее в профиль пользователя
    """
    card_form = PresentCardApplyForm(request.POST)
    if card_form.is_valid():
        code = card_form.cleaned_data.get('code')
        present_card = PresentCard.objects.get(code=code)
        request.session['present_card_id'] = present_card.pk
        Profile.objects.get(user=request.user).profile_cards.add(present_card)

        return JsonResponse({'success': True,
                             'card_amount': present_card.amount})
    else:
        request.session['present_card_id'] = None
        return JsonResponse({'success': False,
                             'form_errors': card_form.errors})


@ajax_required
@require_POST
def cancel_present_card(request):
    """
    Отмена применения подарочной карты к корзине,
    удаление ее из сессии и из пользовательского профиля
    """
    present_card = PresentCard.objects.get(pk=request.session.get('present_card_id'))
    present_card.profile.profile_cards.update(profile_id=None)

    del request.session['present_card_id']
    request.session.modified = True

    return JsonResponse({'success': True,
                         'card_amount': present_card.amount})
