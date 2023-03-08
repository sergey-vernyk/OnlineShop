from django import forms


class CartQuantityForm(forms.Form):
    """
    Форма для указания добавляемого кол-ва товара в корзину
    """

    quantity = forms.IntegerField(initial=1, min_value=1, max_value=10, step_size=1, widget=forms.NumberInput(attrs={
        'style': 'width: 3em'}))
