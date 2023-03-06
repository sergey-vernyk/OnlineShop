from django.shortcuts import render, redirect

from coupons.forms import CouponApplyForm
from .models import Coupon
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


def apply_coupon(request):
    """
    Применение купона со страницы корзины
    """
    now = timezone.now()
    coupon = None
    if request.method == 'POST':
        coupon_form = CouponApplyForm(request.POST)
        if coupon_form.is_valid():
            code = coupon_form.cleaned_data.get('code')
            try:
                coupon = Coupon.objects.get(code__iexact=code,
                                            valid_from__lte=now,
                                            valid_to__gte=now,
                                            active=True)
            except ObjectDoesNotExist:
                request.session['coupon_id'] = None
            else:
                request.session['coupon_id'] = coupon.pk

    return redirect('cart:cart_detail')


def cancel_coupon(request):
    """
    Отмена применения купона к корзине
    и удаление его из сессии
    """
    del request.session['coupon_id']
    request.session.modified = True
    return redirect('cart:cart_detail')
