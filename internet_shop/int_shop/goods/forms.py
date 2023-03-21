from django import forms

from goods.models import Product, Comment, Manufacturer, Property, PropertyCategory


class RatingSetForm(forms.ModelForm):
    """
    Форма для установки рейтинга товара
    """

    class Meta:
        model = Product
        fields = ('star',)
        widgets = {
            'star': forms.Select(attrs={'class': 'form-control form-control-sm w-25'})
        }


class CommentProductForm(forms.ModelForm):
    """
    Форма для написания комментария для товара
    """

    class Meta:
        model = Comment
        fields = ('user_name', 'user_email', 'body')
        widgets = {
            'user_name': forms.TextInput(attrs={'class': 'form-control w-25', 'placeholder': 'Your name'}),
            'user_email': forms.EmailInput(attrs={'class': 'form-control w-25', 'placeholder': 'example@example.com'}),
            'body': forms.Textarea(attrs={'class': 'form-control w-50',
                                          'rows': 3,
                                          'placeholder': 'Type your review...'}),
        }


class FilterByPriceForm(forms.Form):
    """
    Форма для фильтра товаров по цене
    """
    price_min = forms.CharField(widget=forms.TextInput(attrs={'style': 'width:100px'}))
    price_max = forms.CharField(widget=forms.TextInput(attrs={'style': 'width:100px'}))


class FilterByManufacturerForm(forms.Form):
    """
    Форма для выбора одного или нескольких производителей
    """
    manufacturer = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        queryset=Manufacturer.objects.all()
    )


class FilterByPropertyForm(forms.Form):
    """
    Форма для выбора свойств для фильтрации
    """

    battery = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        queryset=Property.objects.filter(category_property__name='Battery')
    )

    display = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        queryset=Property.objects.filter(category_property__name='Display')
    )