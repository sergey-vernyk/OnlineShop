from common.decorators import ajax_required
from account.models import Profile
from coupons.forms import CouponApplyForm
from .models import Coupon
from django.views.decorators.http import require_POST
from django.http.response import JsonResponse
from decimal import Decimal
from django.shortcuts import reverse


@ajax_required
@require_POST
def apply_coupon(request):
    """
    Применение купона со страницы корзины
    и добавление его в профиль пользователя
    """
    coupon_form = CouponApplyForm(request.POST)
    if coupon_form.is_valid():
        code = coupon_form.cleaned_data.get('code')
        coupon = Coupon.objects.get(code=code)
        # попытка добавить купон пользователю в профиль
        # и переход на страницу для входа в систему
        try:
            Profile.objects.get(user=request.user).coupons.add(coupon)
            request.session['coupon_id'] = coupon.pk
        except TypeError:
            return JsonResponse(
                {'success': False,
                 'login_page_url': f'{reverse("login")}?next={reverse("cart:cart_detail")}'},
                status=401
            )

        return JsonResponse({'success': True,
                             'coupon_discount': coupon.discount / Decimal(100)})
    else:
        request.session['coupon_id'] = None
        return JsonResponse({'success': False,
                             'form_errors': coupon_form.errors})


@ajax_required
@require_POST
def cancel_coupon(request):
    """
    Отмена применения купона к корзине,
    удаление его из сессии и из пользовательского профиля
    """
    coupon = Coupon.objects.get(id=request.session['coupon_id'])
    Profile.objects.get(user=request.user).coupons.remove(coupon)

    del request.session['coupon_id']
    request.session.modified = True

    return JsonResponse({'success': True,
                         'coupon_discount': coupon.discount / Decimal(100)})
