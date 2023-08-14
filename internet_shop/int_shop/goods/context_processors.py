from .forms import SearchForm
from .models import Category


def product_categories(request):
    """
    Products categories are displaying on all templates
    """
    return {'categories': Category.objects.all()}


def search_form(request):
    """
    Search form is displaying on all templates
    """
    return {'search_form': SearchForm()}
