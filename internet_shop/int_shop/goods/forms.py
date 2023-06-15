from django import forms

from goods.models import Product, Comment, Manufacturer


class RatingSetForm(forms.ModelForm):
    """
    Форма для установки рейтинга товара
    """

    class Meta:
        model = Product
        fields = ('star',)
        widgets = {
            'star': forms.HiddenInput()
        }


class CommentProductForm(forms.ModelForm):
    """
    Форма для написания комментария для товара
    """

    class Meta:
        model = Comment
        fields = ('user_name', 'user_email', 'body')
        widgets = {
            'user_name': forms.TextInput(attrs={'class': 'comment-field', 'placeholder': 'Your name'}),
            'user_email': forms.EmailInput(attrs={'class': 'comment-field', 'placeholder': 'example@example.com'}),
            'body': forms.Textarea(attrs={'class': 'comment-field-area',
                                          'rows': 3,
                                          'cols': 23,
                                          'placeholder': 'Type your review...'}),
        }

        error_messages = {field: {'required': 'This field must not be empty'} for field in fields}


class FilterByPriceForm(forms.Form):
    """
    Форма для фильтра товаров по цене
    """
    price_min = forms.CharField(widget=forms.TextInput(attrs={'class': 'min-price'}))
    price_max = forms.CharField(widget=forms.TextInput(attrs={'class': 'max-price'}))


class FilterByManufacturerForm(forms.Form):
    """
    Форма для выбора одного или нескольких производителей
    """
    manufacturer = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'check-field-filter'}),
        queryset=Manufacturer.objects.all()
    )


class SortByPriceForm(forms.Form):
    """
    Форма для сортировки товаров по цене
    """
    sorting = forms.ChoiceField(label='Sorting', choices=(
        ('default', 'Price: Default'),
        ('p_asc', 'Price: Low To High'),
        ('p_desc', 'Price: High To Low'),
    ), widget=forms.Select(attrs={'class': 'sorting-select'}))


class SearchForm(forms.Form):
    """
    Форма для поиска товаров на сайте
    """
    query = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'What find?',
                                                          'class': 'search-field-input'}))
