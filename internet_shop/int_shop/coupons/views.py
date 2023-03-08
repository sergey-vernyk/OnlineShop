from django.shortcuts import render, redirect

from account.models import Profile
from coupons.forms import CouponApplyForm
from .models import Coupon
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


def apply_coupon(request):
    """
    Применение купона со страницы корзины
    и добавление его в профиль пользователя
    """
    now = timezone.now()
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
                Profile.objects.get(user=request.user).coupons.add(coupon)

    return redirect('cart:cart_detail')


def cancel_coupon(request):
    """
    Отмена применения купона к корзине,
    удаление его из сессии и из пользовательского профиля
    """
    coupon = Coupon.objects.get(id=request.session['coupon_id'])
    Profile.objects.get(user=request.user).coupons.remove(coupon)

    del request.session['coupon_id']
    request.session.modified = True

    return redirect('cart:cart_detail')
