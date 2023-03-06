from django import forms


class CouponApplyForm(forms.Form):
    """
    Форма для ввода кода купона для скидки
    """
    code = forms.CharField(widget=forms.TextInput(), label='Coupon code')
