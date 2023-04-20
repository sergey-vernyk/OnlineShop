from django import forms

from .models import Delivery, Order


class OrderCreateForm(forms.ModelForm):
    """
    Форма для создания основной информации для заказа
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # переопределение '------' на другое отображение при не выбранной категории
        self.fields['pay_method'].widget.choices[0] = ('', "Not choose")

    prefix = 'order_form'

    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email',
                  'address', 'phone', 'pay_method', 'recipient', 'comment', 'call_confirm')

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@example.com'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Street, Building'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+x (xxx) xxx xx xx'}),
            'pay_method': forms.Select(attrs={'class': 'form-select'}),
            'call_confirm': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any comment...'}),
            'recipient': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name Surname'}),
        }


class DeliveryCreateForm(forms.ModelForm):
    """
    Форма для создания информации о доставке
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # переопределение '------' на другое отображение при не выбранной категории
        self.fields['method'].widget.choices[0] = ('', "Not choose")

    prefix = 'delivery_form'

    class Meta:
        model = Delivery
        fields = ('first_name', 'last_name', 'method', 'office_number', 'delivery_date')

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'office_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'yyyy-mm-dd'}),
        }
