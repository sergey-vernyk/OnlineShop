from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from present_cards.models import PresentCard


class PresentCardApplyForm(forms.Form):
    """
    Form for applying present card coded
    """
    code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Enter code'}), label='Present Card code')

    def clean_code(self):
        """
        Checking validity present card code and error, if present card doesn't valid
        """
        now = timezone.now()
        code = self.cleaned_data.get('code')
        try:
            card = PresentCard.objects.get(code__iexact=code,
                                           valid_from__lte=now,
                                           valid_to__gte=now)
        except ObjectDoesNotExist:
            self.add_error('code', 'Invalid card code')
        else:
            if card.profile is not None:  # if the present card was anybody used
                self.add_error('code', 'The code was already used')
            else:
                return code
