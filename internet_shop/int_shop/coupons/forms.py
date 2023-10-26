from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from coupons.models import Coupon


class CouponApplyForm(forms.Form):
    """
    Form for entering discount coupon code
    """
    code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('Enter code')}), label=_('Coupon code'))

    def clean_code(self):
        """
        Checking validity of coupon code and error, when coupon invalid.
        """
        now = timezone.now()
        code = self.cleaned_data.get('code')
        try:
            Coupon.objects.get(code__iexact=code,
                               valid_from__lte=now,
                               valid_to__gte=now)
        except ObjectDoesNotExist:
            self.add_error('code', _('Invalid coupon code'))
        return code
