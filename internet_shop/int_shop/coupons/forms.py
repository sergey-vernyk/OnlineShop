from django import forms
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from coupons.models import Coupon


class CouponApplyForm(forms.Form):
    """
    Форма для ввода кода купона для скидки
    """
    code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter code'}), label='Coupon code')

    def clean_code(self):
        """
        Проверка валидности кода купона в БД
        и ошибка, если купон не валидный
        """
        now = timezone.now()
        code = self.cleaned_data.get('code')
        try:
            Coupon.objects.get(code__iexact=code,
                               valid_from__lte=now,
                               valid_to__gte=now)
        except ObjectDoesNotExist:
            self.add_error('code', 'Invalid coupon code')
        else:
            return code
