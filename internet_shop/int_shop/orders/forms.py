from django import forms

from orders.models import Order, Delivery


class OrderCreateForm(forms.ModelForm):
    """
    Форма для создания основной информации для заказа
    """
    prefix = 'order_form'

    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email',
                  'address', 'phone', 'pay_method', 'recipient', 'comment', 'call_confirm')

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control w-25'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control w-25'}),
            'email': forms.EmailInput(attrs={'class': 'form-control w-25'}),
            'address': forms.TextInput(attrs={'class': 'form-control w-25'}),
            'phone': forms.TextInput(attrs={'class': 'form-control w-25'}),
            'pay_method': forms.Select(attrs={'class': 'form-select w-25'}),
            'call_confirm': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control w-25', 'rows': 3}),
            'recipient': forms.TextInput(attrs={'class': 'form-control w-25'}),
        }


class DeliveryCreateForm(forms.ModelForm):
    """
    Форма для создания информации о доставке
    """
    prefix = 'delivery_form'

    class Meta:
        model = Delivery
        fields = ('first_name', 'last_name', 'method', 'office_number', 'delivery_date')

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control w-25'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control w-25'}),
            'method': forms.Select(attrs={'class': 'form-select w-25'}),
            'office_number': forms.NumberInput(attrs={'class': 'form-control w-25'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control w-25'}),
        }
