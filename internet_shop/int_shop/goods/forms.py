from django import forms

from common.utils import validate_captcha_text
from goods.models import Product, Comment, Manufacturer
from django.core.validators import ValidationError
from common.moduls_init import redis


class RatingSetForm(forms.ModelForm):
    """
    Form for setting product rating
    """

    class Meta:
        model = Product
        fields = ('star',)
        widgets = {
            'star': forms.HiddenInput()
        }


class CommentProductForm(forms.ModelForm, forms.Form):
    """
    Form for leaving comments for a product
    """
    captcha = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'comment-field-captcha'}))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # override error message of custom field
        self.fields['captcha'].error_messages['required'] = 'This field must not be empty'

    class Meta:
        model = Comment
        fields = ('user_name', 'user_email', 'body', 'captcha')
        widgets = {
            'user_name': forms.TextInput(attrs={'class': 'comment-field', 'placeholder': 'Your name'}),
            'user_email': forms.EmailInput(attrs={'class': 'comment-field', 'placeholder': 'example@example.com'}),
            'body': forms.Textarea(attrs={'class': 'comment-field-area',
                                          'rows': 3,
                                          'cols': 23,
                                          'placeholder': 'Type your review...'}),
        }

        # set the same error message for each field
        error_messages = {field: {'required': 'This field must not be empty'} for field in fields}

    def clean_captcha(self):
        """
        Checking whether user entered correct text from captcha, otherwise raise an exception
        """
        return validate_captcha_text(self.cleaned_data)


class FilterByPriceForm(forms.Form):
    """
    Form for products filter by price
    """
    price_min = forms.CharField(widget=forms.TextInput(attrs={'class': 'min-price'}))
    price_max = forms.CharField(widget=forms.TextInput(attrs={'class': 'max-price'}))


class FilterByManufacturerForm(forms.Form):
    """
    Form for select one or multiple manufacturers
    """
    manufacturer = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'check-field-filter'}),
        queryset=Manufacturer.objects.all()
    )


class SortByPriceForm(forms.Form):
    """
    Form for sorting products by price
    """
    sorting = forms.ChoiceField(label='Sorting', choices=(
        ('default', 'Price: Default'),
        ('p_asc', 'Price: Low To High'),
        ('p_desc', 'Price: High To Low'),
    ), widget=forms.Select(attrs={'class': 'sorting-select'}))


class SearchForm(forms.Form):
    """
    Form for searching products on the site
    """
    query = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'What find?',
                                                          'class': 'search-field-input'}))
