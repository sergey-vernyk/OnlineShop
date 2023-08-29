from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from common.utils import check_phone_number
from .models import Delivery, Order


class OrderCreateForm(forms.ModelForm):
    """
    Форма для создания основной информации для заказа
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # overriding '------' if no category had chosen
        self.fields['pay_method'].widget.choices[0] = ('', "Not choose")

    prefix = 'order_form'

    def clean_phone(self):
        """
        Checking whether phone number is valid in the order
        """
        phone_number_in = self.cleaned_data.get('phone')
        phone_number_output = check_phone_number(phone_number_in)
        if phone_number_output:
            return phone_number_output
        else:
            self.add_error('phone', 'Invalid phone number')

    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email',
                  'phone', 'pay_method', 'address', 'comment', 'call_confirm')

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'order-field'}),
            'last_name': forms.TextInput(attrs={'class': 'order-field'}),
            'email': forms.EmailInput(attrs={'class': 'order-field', 'placeholder': 'example@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'order-field', 'placeholder': '+country code ...'}),
            'pay_method': forms.Select(attrs={'class': 'order-field-choice'}),
            'address': forms.TextInput(attrs={'class': 'order-field', 'placeholder': 'City, Street, Building'}),
            'call_confirm': forms.CheckboxInput(attrs={'class': 'check-order-field'}),
            'comment': forms.Textarea(attrs={'class': 'order-field-comment',
                                             'rows': 3,
                                             'cols': 28,
                                             'placeholder': 'Any comment...'}),
        }

        error_messages = {
            'email': {
                'invalid': 'Enter a valid email address',
                'required': 'This field must not be empty',
            },
        }

        # adding errors messages for multiple fields
        error_messages.update(
            {k: {'required': 'This field must not be empty'} for k in
             ('first_name', 'last_name', 'address', 'phone', 'pay_method')}
        )


class DeliveryCreateForm(forms.ModelForm):
    """
    Forms using for creation info about delivery
    """

    delivery_date = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS,
                                    widget=forms.DateInput(attrs={'class': 'order-field', 'placeholder': 'dd-mm-yyyy'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # overriding '------' if no category had chosen
        self.fields['method'].widget.choices[0] = ('', "Not choose")
        self.fields['service'].widget.choices[0] = ('', "Not choose")
        # overriding default error field message
        self.fields['delivery_date'].error_messages['required'] = 'This field must not be empty'

    prefix = 'delivery_form'

    class Meta:
        model = Delivery
        fields = ('first_name', 'last_name', 'service', 'method', 'office_number', 'delivery_date')

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'order-field'}),
            'last_name': forms.TextInput(attrs={'class': 'order-field'}),
            'service': forms.Select(attrs={'class': 'order-field-choice'}),
            'method': forms.Select(attrs={'class': 'order-field-choice'}),
            'office_number': forms.NumberInput(attrs={'class': 'order-field',
                                                      'min': 1}),
        }

        error_messages = {
            field: {'required': 'This field must not be empty'} for field in fields
        }

    def clean_delivery_date(self):
        """
        Checking delivery date, whether date not less than today
        """
        date_now = timezone.now().date()
        date = self.cleaned_data.get('delivery_date')

        if date < date_now:
            raise ValidationError('Date must be grater or equal than today date', code='past_date')

        return date
