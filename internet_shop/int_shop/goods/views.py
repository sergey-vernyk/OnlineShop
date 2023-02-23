from django.shortcuts import render
from django.views.generic import ListView, DetailView

from goods.models import Product, Category


class ProductListView(ListView):
    """
    Список все товаров
    """
    model = Product
    template_name = 'goods/product/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.kwargs:  # если передана категория
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))
        return context

    def get_queryset(self):
        if self.kwargs:  # если передана категория
            return super(ProductListView, self).get_queryset().filter(category__slug=self.kwargs['category_slug'])
        return super().get_queryset()


class ProductDetailView(DetailView):
    """
    Подробное описание товара
    """
    model = Product
    template_name = 'goods/product/detail.html'
    slug_url_kwarg = 'product_slug'
    pk_url_kwarg = 'product_pk'
