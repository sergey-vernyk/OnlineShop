from .forms import SearchForm
from .models import Category


def product_categories(request):
    """
    Функция делает доступными категории
    в навигационном меню на любом шаблоне странице
    """
    return {'categories': Category.objects.all()}


def search_form(request):
    """
    Функция делает доступной строку поиска на
    каждой страницы
    """
    return {'search_form': SearchForm()}
