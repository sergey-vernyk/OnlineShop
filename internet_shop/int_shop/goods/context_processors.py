from .models import Category


def product_categories(request):
    """
    Функция делает доступными категории
    в навигационном меню на любом шаблоне странице
    """
    return {'categories': Category.objects.all()}
