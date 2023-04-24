import math
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.conf import settings
from account.models import Profile
from django.views.decorators.http import require_POST
from django.http.response import JsonResponse
from goods.forms import RatingSetForm, CommentProductForm, SortByPriceForm
from cart.forms import CartQuantityForm
from goods.logic import distribute_properties_from_request, get_page_obj
from goods.models import Product, Category, Favorite
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .utils import GoodsContextMixin
import redis
from common.decorators import ajax_required

# инициализация Redis
r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB)


class ProductListView(ListView, GoodsContextMixin):
    """
    Список всех товаров
    """
    model = Product
    template_name = 'goods/product/list.html'
    context_object_name = 'products'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'category_slug' in self.kwargs:  # если передана категория
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))
            context = self.add_to_context(context, self.kwargs)

        context['sorting_by_price'] = SortByPriceForm()
        return context

    def get_queryset(self):
        if 'category_slug' in self.kwargs:  # если передана категория
            return super().get_queryset().filter(category__slug=self.kwargs['category_slug'])
        return super().get_queryset()


class ProductDetailView(FormMixin, DetailView):
    """
    Подробное описание товара
    """
    model = Product
    template_name = 'goods/product/detail.html'
    slug_url_kwarg = 'product_slug'
    pk_url_kwarg = 'product_pk'
    context_object_name = 'product'
    form_class = RatingSetForm  # форма добавляется из FormMixin

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        """
        Возвращает URL для перехода после обработки валидной формы
        """
        return reverse('goods:product_detail', kwargs={'product_pk': self.kwargs['product_pk'],
                                                       'product_slug': self.kwargs['product_slug']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rating_form'] = self.form_class  # добавляем форму рейтинга в контекст
        context['comment_form'] = CommentProductForm()  # добавляем форму комментария в контекст
        context['quantity_form'] = CartQuantityForm()  # добавляем форму кол-ва товаров в контекст
        # получение всех объектов Profile, которые комментировали текущий товар (оптимизация!!)
        context['comments'] = self.object.comments.select_related('profile').order_by('-created')
        # получение всех объектов Property, которые принадлежат текущему товару (оптимизация!!)
        context['properties'] = self.object.properties.select_related('category_property')
        # если пользователь аутентифицирован, то заполнить имя, почту в форме отправки комментария
        if self.request.user.is_authenticated:
            context['comment_form'].fields['user_name'].initial = self.request.user.first_name
            context['comment_form'].fields['user_email'].initial = self.request.user.email
            context['is_in_favorite'] = self.is_in_favorite()
        return context

    def is_in_favorite(self) -> bool:
        """
        Возвращает true/false находится ли этот товар
        у текущего пользователя в избранном
        """
        profile = Profile.objects.get(user=self.request.user)  # достаем профиль привязанный к текущему пользователю
        try:
            fav_obj = Favorite.objects.get(profile=profile)  # достаем объект избранных товаров привязанного к профилю
        except ObjectDoesNotExist:
            return False
        return self.object in fav_obj.product.prefetch_related()  # возвращаем результат, есть ли товар в избранном

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        #  если пользователь аутентифицирован на сайте и отправляет комментарий
        if 'comment_sent' in request.POST:
            # присвоить объект представлению
            form = self.get_form(form_class=CommentProductForm)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.product = self.object  # привязка комментария к текущему товару
                # получение текущего профиля пользователя сайта
                # привязка комментария к текущему профилю
                profile_instance = Profile.objects.get(user__id=request.user.pk)
                new_comment.profile = profile_instance
                new_comment.save()  # сохранение в базе
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        """
        Метод используется для увеличения кол-ва
        просмотров текущего товара при переходе на
        детальную информацию о нем
        """
        self.object = self.get_object()
        # увеличение кол-ва просмотров товара на 1 при его просмотре
        r.hincrby(f'product_id:{self.object.pk}', 'views', 1)
        return super().get(request, *args, **kwargs)


@login_required
@require_POST
@ajax_required
def add_or_remove_product_favorite(request) -> JsonResponse:
    """
    Добавление товара в избранное или удаление его
    """
    product_id = request.POST.get('product_id')
    action = request.POST.get('action')

    product = Product.objects.get(pk=product_id)
    profile = Profile.objects.get(user=request.user)

    if action == 'add':
        Favorite.objects.get(profile=profile).product.add(product)
    elif action == 'remove':
        Favorite.objects.get(profile=profile).product.remove(product)

    # кол-во товаров в избранном для текущего profile
    amount_prods = Favorite.objects.get(profile=profile).product.prefetch_related().count()

    return JsonResponse({'success': True,
                         'amount_prods': amount_prods})


class FilterResultsView(ListView, GoodsContextMixin):
    """
    Отображение результатов после применения фильтра
    """
    model = Product
    template_name = 'filter_result_list.html'
    context_object_name = 'products'
    paginate_by = 3

    def get(self, request, *args, **kwargs):
        if request.GET:  # если была подтверждена форма с критериями фильтров
            if 'price_max' and 'price_min' in request.GET:
                price_min = request.GET.get('price_min')
                price_max = request.GET.get('price_max')
                self.kwargs['filter_price'] = (price_min, price_max)

            if 'manufacturer' in request.GET:
                manufacturers = request.GET.getlist('manufacturer')
                self.kwargs['filter_manufacturers'] = manufacturers

            if 'props' in request.GET:
                properties = request.GET.getlist('props')
                self.kwargs['props'] = properties

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # отбор товаров только определенной категории
        result_queryset = Product.objects.filter(category__slug=self.kwargs['category_slug'])

        # отбор товаров по цене
        if 'filter_price' in self.kwargs:
            min_price = self.kwargs.get('filter_price')[0]
            max_price = self.kwargs.get('filter_price')[1]
            result_queryset = result_queryset.filter(price__gte=min_price, price__lte=max_price)
        # отбор товаров по производителю
        if 'filter_manufacturers' in self.kwargs:
            manufacturers = self.kwargs.get('filter_manufacturers')
            result_queryset = result_queryset.filter(manufacturer_id__in=manufacturers)
        # отбор товаров по свойствам
        if 'props' in self.kwargs:
            properties = self.kwargs.get('props')
            result_dict = distribute_properties_from_request(properties)

            # получение в queryset только уникальных результатов
            result_queryset = result_queryset.distinct().filter(
                properties__category_property__id__in=result_dict['ids'],
                properties__name__in=result_dict['names'],
                properties__text_value__in=result_dict['text_values'],
                properties__numeric_value__in=result_dict['numeric_values']
            )

        return result_queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'category_slug' in self.kwargs:
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))

        context = self.add_to_context(context, self.kwargs)
        context['filter_manufacturers'].fields['manufacturer'].initial = self.kwargs.get('filter_manufacturers')
        return context


def promotions_list(request):
    """
    Список товаров, которые отмечены как акционные
    """
    prom_products = Product.objects.filter(promotional=True)
    page = request.GET.get('page')  # получаем текущую страницу из запроса
    # пагинация списка
    page_obj = get_page_obj(per_pages=1, page=page, queryset=prom_products)

    products = page_obj.object_list  # список товаров на выбранной странице
    return render(request, 'goods/promotions.html', {'products': products,
                                                     'page_obj': page_obj})


def new_list(request):
    """
    Список товаров, которые добавлены на сайт
    2 недели назад и считаются новыми
    """
    now = timezone.now()
    diff = now - timezone.timedelta(weeks=2)

    prom_products = Product.objects.filter(created__gt=diff)
    page = request.GET.get('page')  # получаем текущую страницу из запроса
    page_obj = get_page_obj(per_pages=1, page=page, queryset=prom_products)

    products = page_obj.object_list  # список товаров на выбранной странице
    return render(request, 'goods/new.html', {'products': products,
                                              'page_obj': page_obj})


def popular_list(request, category_slug: str = None):  # TODO refactoring
    """
    Список популярных товаров из категории category_slug
    или список таких товаров со всех категорий на сайте
    """
    category_name = ''
    page = request.GET.get('page')  # получаем текущую страницу из запроса

    amount_products = r.llen('products_ids')  # кол-во id товаров на сайте
    products_ids = [int(pk) for pk in r.lrange('products_ids', 0, amount_products)]  # получение этих id

    # получение всех товаров и связанных с ними категорий и сортировка их по полученных id
    products = Product.objects.select_related('category').in_bulk(products_ids)
    # словарь с ключами id товара и значениями кол-ва его просмотров и категории товара
    # {pk: {category: str, views: int}}
    products_views = {}
    for pk, product in zip(products_ids, (products[p] for p in products_ids)):
        products_views[pk] = {
            'views': int(r.hget(f'product_id:{pk}', 'views') or 0),
            'category': product.category.slug
        }

    # сортировка словаря по уменьшению кол-ва просмотров
    products_views_sorted = {
        pk: {'views': data['views'], 'category': data['category']}
        for pk, data in sorted(products_views.items(), key=lambda x: x[1]['views'], reverse=True)
    }

    products_ids_sorted = [pk for pk in products_views_sorted.keys()]  # ключи отсортированных товаров
    # словарь с отсортированными товарами по кол-ву просмотров
    products = Product.objects.in_bulk(products_ids_sorted)

    if category_slug:  # фильтр товаров по категории
        product_list = [
            products[pk] for pk in products_ids_sorted
            if category_slug in products_views_sorted[pk]['category']
        ]
        category_name = Category.objects.get(slug=category_slug)
    else:
        product_list = [products[pk] for pk in products_ids_sorted]
    # пагинация списка товаров
    page_obj = get_page_obj(per_pages=2, page=page, queryset=product_list)
    products = page_obj.object_list

    return render(request, 'goods/popular_list.html', {'products': products,
                                                       'page_obj': page_obj,
                                                       'category_name': category_name})


def product_ordering(request, category_slug: str = 'all', page: int = 1):
    """
    Сортировка товаров по цене, asc и desc
    """
    products = None
    category = None
    sort = None
    sorting_by_price = SortByPriceForm()  # добавляем пустую форму на страницу после её подтверждения

    if request.method == 'GET':
        sort = request.GET.get('sort')

        if sort == 'p_asc' or sort == 'p_desc':
            if category_slug != 'all':  # если передана категория
                category = Category.objects.get(slug=category_slug)
                products = Product.objects.filter(category=category).order_by('price' if sort == 'p_asc' else '-price')
            else:
                products = Product.objects.all().order_by('price' if sort == 'p_asc' else '-price')
        else:
            products = Product.objects.all()

    # пагинация
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)
    products = page_obj.object_list

    return render(request, 'goods/product/list.html', {'products': products,
                                                       'category': category,
                                                       'sorting_by_price': sorting_by_price,
                                                       'selected_sort': sort,
                                                       'page_obj': page_obj,
                                                       'is_paginated': page_obj.has_other_pages(),
                                                       'is_sorting': True,
                                                       })


@require_POST
@ajax_required
def set_product_rating(request) -> JsonResponse:
    """
    Функция выставляет рейтинг товара
    при помощи запроса ajax
    """
    star = Decimal(request.POST.get('star'))
    product_id = request.POST.get('product_id')
    product = Product.objects.get(pk=product_id)
    current_rating = product.rating
    if not current_rating:
        product.rating = Decimal(star)
    else:  # расчет среднего рейтинга товара
        current_rating = math.ceil((star + current_rating) / 2)
        product.rating = current_rating
    product.save(update_fields=['rating'])  # сохранение в базе

    return JsonResponse({'success': True,
                         'current_rating': current_rating})
