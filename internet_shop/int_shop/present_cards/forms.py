from typing import Union

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from present_cards.models import PresentCard


class PresentCardApplyForm(forms.Form):
    """
    Form for applying present card code.
    """
    code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('Enter code')}), label=_('Present Card code'))

    def clean_code(self) -> Union[str, None]:
        """
        Checking validity present card code and error, if present card doesn't valid.
        """
        now = timezone.now()
        code = self.cleaned_data.get('code')
        try:
            card = PresentCard.objects.get(code__iexact=code,
                                           valid_from__lte=now,
                                           valid_to__gte=now)
        except ObjectDoesNotExist:
            self.add_error('code', _('Invalid card code'))
        else:
            if card.profile is None:  # if the present card was not by anybody used
                return code

        self.add_error('code', _('The code was already used'))
