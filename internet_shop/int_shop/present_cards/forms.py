from django import forms
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from present_cards.models import PresentCard


class PresentCardApplyForm(forms.Form):
    """
    Форма для применения кода подарочной карты
    """
    code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter code'}), label='Present Card code')

    def clean_code(self):
        """
        Проверка валидности кода подарочной карты в БД
        и ошибка, если карта не валидный
        """
        now = timezone.now()
        code = self.cleaned_data.get('code')
        try:
            card = PresentCard.objects.get(code__iexact=code,
                                           valid_from__lte=now,
                                           valid_to__gte=now,
                                           active=True)
        except ObjectDoesNotExist:
            self.add_error('code', 'Invalid card code')
        else:
            if card.profile is not None:  # если уже был кем-то использован
                self.add_error('code', 'The code was already used')
            else:
                return code
