from django import forms


class CartQuantityForm(forms.Form):
    """
    Форма для указания добавляемого кол-ва товара в корзину
    """

    quantity = forms.IntegerField(min_value=0, max_value=10, step_size=1, widget=forms.NumberInput(attrs={
        'style': 'width: 2em'}))
