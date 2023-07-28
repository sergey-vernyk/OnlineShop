from django import forms
from django.utils import timezone
from .models import Delivery, Order
import phonenumbers
from phonenumbers import carrier
from django.conf import settings
from django.core.exceptions import ValidationError


class OrderCreateForm(forms.ModelForm):
    """
    Форма для создания основной информации для заказа
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # переопределение '------' на другое отображение при не выбранной категории
        self.fields['pay_method'].widget.choices[0] = ('', "Not choose")

    prefix = 'order_form'

    def clean_phone(self):
        """
        Валидация номера телефона в заказе
        """
        phone_number_in = self.cleaned_data.get('phone')
        phone_number_output = ''.join(num.strip('()') for num in phone_number_in.split())
        phone_number_parse = phonenumbers.parse(phone_number_output, 'UA')
        carrier_of_number = carrier.name_for_number(phone_number_parse, 'en')
        if phonenumbers.is_possible_number(phone_number_parse) and carrier_of_number in (
                'Kyivstar',
                'Vodafone',
                'lifecell'
        ):
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

        # множественное добавление текста ошибки для полей
        error_messages.update(
            {k: {'required': 'This field must not be empty'} for k in
             ('first_name', 'last_name', 'address', 'phone', 'pay_method')}
        )


class DeliveryCreateForm(forms.ModelForm):
    """
    Форма для создания информации о доставке
    """

    delivery_date = forms.DateField(input_formats=settings.DATE_INPUT_FORMATS,
                                    widget=forms.DateInput(attrs={'class': 'order-field', 'placeholder': 'dd-mm-yyyy'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # переопределение '------' на другое отображение при не выбранной категории
        self.fields['method'].widget.choices[0] = ('', "Not choose")
        self.fields['service'].widget.choices[0] = ('', "Not choose")
        # переопределение стандартного сообщения об ошибке поля
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
        Проверка даты доставки на то, что
        она не меньше сегодняшней даты
        """
        date_now = timezone.now().date()
        date = self.cleaned_data.get('delivery_date')

        if date < date_now:
            raise ValidationError('Date must be grater or equal than today date', code='past_date')

        return date
