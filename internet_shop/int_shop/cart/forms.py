from django import forms


class CartQuantityForm(forms.Form):
    """
    Form for entering product quantity to will add to the cart
    """

    quantity = forms.IntegerField(initial=1,
                                  min_value=1,
                                  max_value=10,
                                  step_size=1, widget=forms.NumberInput(attrs={'class': 'qnty-field'}))
