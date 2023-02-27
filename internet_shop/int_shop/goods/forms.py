from django import forms

from goods.models import Product, Comment


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
            'user_email': forms.EmailInput(attrs={'class': 'form-control w-25', 'placeholder': 'example@exmple.com'}),
            'body': forms.Textarea(attrs={'class': 'form-control w-50',
                                          'rows': 3,
                                          'placeholder': 'Type your review...'}),
        }
