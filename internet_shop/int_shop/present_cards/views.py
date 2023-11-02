from django.http.response import JsonResponse
from django.views.decorators.http import require_POST

from account.models import Profile
from common.decorators import ajax_required
from common.decorators import auth_profile_required
from present_cards.forms import PresentCardApplyForm
from present_cards.models import PresentCard


@auth_profile_required
@ajax_required
@require_POST
def apply_present_card(request):
    """
    Apply present card and add it to profile.
    """
    card_form = PresentCardApplyForm(request.POST)
    if card_form.is_valid():
        code = card_form.cleaned_data.get('code')
        present_card = PresentCard.objects.get(code=code)
        request.session['present_card_id'] = present_card.pk
        Profile.objects.get(user=request.user).profile_cards.add(present_card)

        return JsonResponse({'success': True,
                             'card_amount': present_card.amount})
    request.session['present_card_id'] = None
    return JsonResponse({'success': False,
                         'form_errors': card_form.errors})


@auth_profile_required
@ajax_required
@require_POST
def cancel_present_card(request):
    """
    Cancel applied present card, delete this card from session and from profile.
    """
    present_card = PresentCard.objects.get(pk=request.session.get('present_card_id'))
    present_card.profile.profile_cards.update(profile_id=None)

    del request.session['present_card_id']
    request.session.modified = True

    return JsonResponse({'success': True,
                         'card_amount': present_card.amount})
