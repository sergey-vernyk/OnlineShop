from decimal import Decimal

from django.http.response import JsonResponse
from django.views.decorators.http import require_POST

from account.models import Profile
from common.decorators import ajax_required, auth_profile_required
from coupons.forms import CouponApplyForm
from .models import Coupon


@auth_profile_required
@ajax_required
@require_POST
def apply_coupon(request):
    """
    Apply coupon and add it to profile.
    """
    coupon_form = CouponApplyForm(request.POST)
    if coupon_form.is_valid():
        code = coupon_form.cleaned_data.get('code')
        coupon = Coupon.objects.get(code=code)
        Profile.objects.get(user=request.user).coupons.add(coupon)
        request.session['coupon_id'] = coupon.pk

        return JsonResponse({'success': True,
                             'coupon_discount': coupon.discount / Decimal(100)})

    request.session['coupon_id'] = None
    return JsonResponse({'success': False,
                         'form_errors': coupon_form.errors})


@auth_profile_required
@ajax_required
@require_POST
def cancel_coupon(request):
    """
    Cancel applied coupon and delete it from session and profile
    """
    coupon = Coupon.objects.get(id=request.session['coupon_id'])
    Profile.objects.get(user=request.user).coupons.remove(coupon)

    del request.session['coupon_id']
    request.session.modified = True

    return JsonResponse({'success': True,
                         'coupon_discount': coupon.discount / Decimal(100)})
