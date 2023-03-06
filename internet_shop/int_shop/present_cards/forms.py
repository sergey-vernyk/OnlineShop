from django import forms


class PresentCardApplyForm(forms.Form):
    """
    Форма для применения кода подарочной карты
    """
    code = forms.CharField(widget=forms.TextInput, label='Present Card code')
