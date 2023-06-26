import redis
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from account.models import Profile
from django.views.decorators.http import require_POST
from django.http.response import JsonResponse
from goods.forms import (
    RatingSetForm,
    CommentProductForm,
    SortByPriceForm,
    SearchForm,
    FilterByManufacturerForm,
    FilterByPriceForm,
)
from cart.forms import CartQuantityForm
from goods.models import Product, Category, Favorite, Comment
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .filters import get_max_min_price
from .property_filters import get_property_for_category
from .utils import (
    distribute_properties_from_request,
    get_page_obj,
    get_collections_with_manufacturers_info,
    get_products_sorted_by_views
)
from common.decorators import ajax_required, auth_profile_required
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, QuerySet
from django.conf import settings

# инициализация Redis
r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB_NUM,
                username=settings.REDIS_USER,
                password=settings.REDIS_PASSWORD)


class ProductListView(ListView):
    """
    Список всех товаров
    """
    model = Product
    template_name = 'goods/product/list.html'
    context_object_name = 'products'
    paginate_by = 3

    def __init__(self):
        """
        Переопределение метода для добавления
        экземпляра Profile, необходимого для обозначения на карточках товара
        информации о нахождении или отсутствии товара в избранном для данного Profile
        """
        super().__init__()
        self.profile = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = 'mainlist'
        if 'category_slug' in self.kwargs:  # если передана категория
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))
            context['filter_manufacturers'] = FilterByManufacturerForm()

            context['category_properties'] = get_property_for_category(context['category'].name)

            if 'filter_price' in self.kwargs:
                min_price = Decimal(self.kwargs['filter_price'][0])
                max_price = Decimal(self.kwargs['filter_price'][1])
            else:
                max_price, min_price = get_max_min_price(category_slug=self.kwargs.get('category_slug'))

            context['filter_price'] = FilterByPriceForm(initial={
                'price_min': min_price,
                'price_max': max_price
            })

            category_products = self.get_queryset()
            manufacturers_info = get_collections_with_manufacturers_info(qs=category_products)
            # обновление queryset производителя
            context['filter_manufacturers'].fields['manufacturer'].queryset = next(manufacturers_info)
            context['manufacturers_prod_qnty'] = next(manufacturers_info)  # кол-во товаров каждого производителя

        if self.request.user.is_authenticated:
            context['favorites'] = self.profile.profile_favorite.product.prefetch_related()

        context['sorting_by_price'] = SortByPriceForm()
        context['search_form'] = SearchForm(initial={'query': self.request.GET.get('query')})
        return context

    def get_queryset(self):
        if ('category_slug' and 'search_result') in self.kwargs:  # если передана категория и был поиск
            return self.kwargs.get('search_result')
        if 'category_slug' in self.kwargs:
            return super().get_queryset().filter(category__slug=self.kwargs['category_slug'])

        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        """
        Установка в атрибут profile гостевого или аутентифицированного пользователя
        """
        if request.user.is_authenticated:
            self.profile = Profile.objects.get(user=request.user)
        else:
            self.profile = Profile.objects.get(user__username='guest_user')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Метод используется для поиска по сайту
        и для обычной загрузки главной страницы сайта
        """
        query = request.GET.get('query')
        category_slug = self.kwargs.get('category_slug')

        # если был запрос на поиск
        if 'query' in request.GET:
            result = self._get_query_results(query, category_slug)
            self.kwargs['search_result'] = [product for product in result.values()]

        return super().get(request, *args, **kwargs)

    @staticmethod
    def _get_query_results(query: str, category_slug: str = None) -> dict:
        """
        Метод для получения результатов поиска.
        query - текст запроса
        """
        if category_slug:
            q = Q(category__slug=category_slug, similarity__gte=0.3)
        else:
            q = Q(similarity__gte=0.3)

        products = Product.objects.annotate(
            similarity=TrigramSimilarity('name', query), ).filter(q).order_by('-similarity')

        product_ids = [product.pk for product in products]
        # кол-во просмотров найденных товаров и сортировка их id по уменьшению просмотров
        product_views = [int(r.hget(f'product_id:{pk}', 'views')) for pk in product_ids]
        sorted_ids_by_views = [pk for pk, views in sorted(zip(product_ids, product_views), key=lambda x: -x[1])]
        return products.in_bulk(sorted_ids_by_views)


class ProductDetailView(DetailView, FormMixin):
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
        self.profile = None

    def get_success_url(self):
        """
        Возвращает URL для перехода после обработки валидной формы
        """
        return reverse('goods:product_detail', kwargs={'product_pk': self.kwargs['product_pk'],
                                                       'product_slug': self.kwargs['product_slug']})

    def dispatch(self, request, *args, **kwargs):
        """
        Установка в атрибут profile гостевого или аутентифицированного пользователя
        """
        if request.user.is_authenticated:
            self.profile = Profile.objects.get(user=request.user)
        else:
            self.profile = Profile.objects.get(user__username='guest_user')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rating_form'] = self.form_class  # добавляем форму рейтинга в контекст
        context['comment_form'] = CommentProductForm()  # добавляем форму комментария в контекст
        context['quantity_form'] = CartQuantityForm()  # добавляем форму кол-ва товара в контекст
        # получение всех объектов Profile, которые комментировали текущий товар и оценивали комментарий к товару
        context['comments'] = self.object.comments.prefetch_related('profile',
                                                                    'profiles_likes',
                                                                    'profiles_unlikes').order_by('-created')
        # получение всех объектов Property, которые принадлежат текущему товару
        context['properties'] = self.object.properties.select_related('category_property')
        # если пользователь аутентифицирован, то заполнить имя, почту в форме отправки комментария
        if self.request.user.is_authenticated:
            context['comment_form'].fields['user_name'].initial = self.request.user.first_name
            context['comment_form'].fields['user_email'].initial = self.request.user.email
            context['is_in_favorite'] = self.is_in_favorite()
            context['profile_rated_comments'] = self.get_profile_rated_comments()
        return context

    def is_in_favorite(self) -> bool:
        """
        Возвращает true/false находится ли этот товар
        у текущего пользователя в избранном
        """
        try:
            # получение объекта избранных товаров привязанного к профилю
            fav_obj = Favorite.objects.get(profile=self.profile)
        except ObjectDoesNotExist:
            return False
        return self.object in fav_obj.product.prefetch_related()  # возвращаем результат, есть ли товар в избранном

    def get_profile_rated_comments(self) -> dict:
        """
        Возвращает id комментариев, под которыми текущий
        пользователь (profile) установил like или dislike
        """
        liked_comments = self.profile.comments_liked.all()
        unliked_comments = self.profile.comments_unliked.all()
        return {'liked_comments': [c.pk for c in liked_comments],
                'unliked_comments': [c.pk for c in unliked_comments]}

    @auth_profile_required
    def post(self, request, *args, **kwargs):
        # если AJAX запрос
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            comment_id = request.POST.get('comment_id')
            action = request.POST.get('action')  # like/unlike
            comment = Comment.objects.get(pk=comment_id)

            liked_comments = self.profile.comments_liked.all()
            unliked_comments = self.profile.comments_unliked.all()

            # установка like/dislike для комментария
            if action == 'like':
                if comment in liked_comments:
                    comment.profiles_likes.remove(self.profile)
                else:
                    comment.profiles_likes.add(self.profile)
                    comment.profiles_unlikes.remove(self.profile)

            elif action == 'unlike':
                if comment in unliked_comments:
                    comment.profiles_unlikes.remove(self.profile)
                else:
                    comment.profiles_unlikes.add(self.profile)
                    comment.profiles_likes.remove(self.profile)

            new_count_likes = comment.profiles_likes.count()
            new_count_unlikes = comment.profiles_unlikes.count()
            return JsonResponse({'success': True,
                                 'new_count_likes': new_count_likes,
                                 'new_count_unlikes': new_count_unlikes})
        else:
            self.object = self.get_object()
            form = self.get_form(form_class=CommentProductForm)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.product = self.object  # привязка комментария к текущему товару
                new_comment.profile = self.profile
                new_comment.save()  # сохранение в базе
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

    def form_invalid(self, form):
        """
        Переопределение метода для добавления в контекст
        формы с ошибками
        """
        context = self.get_context_data()
        context.update(comment_form=form)
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        """
        Метод используется для увеличения кол-ва
        просмотров текущего товара при переходе на
        детальную информацию о нем
        """
        object_pk = self.kwargs.get(self.pk_url_kwarg)  # получение id товара из аргументов URL
        # увеличение кол-ва просмотров товара на 1 при его просмотре
        # задание времени жизни ключа из Redis - удаление товаров из просмотренных пользователем через 7 дней
        # добавление товара в множество просмотренных товаров пользователем
        r.hincrby(f'product_id:{object_pk}', 'views', 1)
        r.expire(f'profile_id:{self.profile.pk}', time=604800, nx=True)
        r.sadd(f'profile_id:{self.profile.pk}', object_pk)
        return super().get(request, *args, **kwargs)


@auth_profile_required
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
        profile.profile_favorite.product.add(product)
    elif action == 'remove':
        profile.profile_favorite.product.remove(product)

    # кол-во товаров в избранном для текущего profile
    amount_prods = profile.profile_favorite.product.all().count()

    return JsonResponse({'success': True,
                         'amount_prods': amount_prods})


class FilterResultsView(ListView):
    """
    Отображение результатов после применения фильтра
    """
    model = Product
    template_name = 'goods/product/list.html'
    context_object_name = 'products'
    paginate_by = 3

    def __init__(self):
        super().__init__()
        self.filter_qs = None  # queryset с товарами полученными после фильтра

    @property
    def queryset_filter(self):
        return self.filter_qs

    @queryset_filter.setter
    def queryset_filter(self, qs):
        if isinstance(qs, QuerySet):
            self.filter_qs = qs
        else:
            raise TypeError(f'Argument qs not QuerySet instance, ({type(qs).__name__}) was provided')

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
        props_dict = {}
        lookups = Q(category__slug=self.kwargs['category_slug'])

        # отбор товаров по цене
        if 'filter_price' in self.kwargs:
            min_price = self.kwargs.get('filter_price')[0]
            max_price = self.kwargs.get('filter_price')[1]
            lookups &= Q(price__gte=min_price, price__lte=max_price)
        # отбор товаров по производителю
        if 'filter_manufacturers' in self.kwargs:
            manufacturers = self.kwargs.get('filter_manufacturers')
            lookups &= Q(manufacturer_id__in=manufacturers)
        # отбор товаров по свойствам
        if 'props' in self.kwargs:
            properties = self.kwargs.get('props')
            props_dict = distribute_properties_from_request(properties)
        # TODO fix
        # получение в queryset только уникальных результатов
        result_queryset = Product.objects.distinct().filter(
            lookups,
            properties__category_property__id__in=props_dict['ids'],
            properties__name__in=props_dict['names'],
            properties__text_value__in=props_dict['text_values'],
            properties__numeric_value__in=props_dict['numeric_values'],
        )

        self.queryset_filter = result_queryset  # сохранение queryset в property
        return result_queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = 'filter_list'
        if 'category_slug' in self.kwargs:
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))

            context['category_properties'] = get_property_for_category(context['category'].name,
                                                                       self.queryset_filter)

            if 'filter_price' in self.kwargs:
                min_price = Decimal(self.kwargs['filter_price'][0])
                max_price = Decimal(self.kwargs['filter_price'][1])
            else:
                max_price, min_price = get_max_min_price(category_slug=self.kwargs.get('category_slug'))

            context['filter_price'] = FilterByPriceForm(initial={
                'price_min': min_price,
                'price_max': max_price,
            })

            category_products = self.queryset_filter  # все товары для категории, которые были отфильтрованы
            manufacturers_info = get_collections_with_manufacturers_info(qs=category_products)

            # обновление queryset и отметка выбранных производителя
            context['filter_manufacturers'] = FilterByManufacturerForm(initial={
                'manufacturer': self.kwargs.get('filter_manufacturers')

            })
            context['filter_manufacturers'].fields['manufacturer'].queryset = next(manufacturers_info)
            context['manufacturers_prod_qnty'] = next(manufacturers_info)  # кол-во товаров каждого производителя
        context['sorting_by_price'] = SortByPriceForm()

        return context


def promotion_list(request, category_slug: str = None):
    """
    Список товаров, которые отмечены как акционные
    """
    category = Category.objects.get(slug=category_slug) if category_slug else ''
    lookup = Q(category__slug=category_slug, promotional=True) if category_slug else Q(promotional=True)
    products = Product.objects.filter(lookup)
    page = request.GET.get('page')  # получаем текущую страницу из запроса
    # пагинация списка
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)
    products = page_obj.object_list  # список товаров на выбранной странице
    sorting_by_price = SortByPriceForm()

    return render(request, 'goods/product/navs_categories_list.html', {'products': products,
                                                                       'page_obj': page_obj,
                                                                       'category': category,
                                                                       'sorting_by_price': sorting_by_price,
                                                                       'is_paginated': page_obj.has_other_pages(),
                                                                       'is_sorting': False,
                                                                       'place': 'promotion'})


def new_list(request, category_slug: str = None):
    """
    Список товаров, которые добавлены на сайт
    2 недели назад и считаются новыми
    """
    category = Category.objects.get(slug=category_slug) if category_slug else ''
    now = timezone.now()
    diff = now - timezone.timedelta(weeks=2)
    lookup = Q(created__gt=diff, category__slug=category_slug) if category_slug else Q(created__gt=diff)

    products = Product.objects.filter(lookup)
    r.hset('new_prods', 'ids', ','.join(str(prod.pk) for prod in products))  # сохранение id новых товаров в redis
    page = request.GET.get('page')  # получаем текущую страницу из запроса
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)

    products = page_obj.object_list  # список товаров на выбранной странице
    sorting_by_price = SortByPriceForm()

    return render(request, 'goods/product/navs_categories_list.html', {'products': products,
                                                                       'page_obj': page_obj,
                                                                       'category': category,
                                                                       'sorting_by_price': sorting_by_price,
                                                                       'is_paginated': page_obj.has_other_pages(),
                                                                       'is_sorting': False,
                                                                       'place': 'new'})


def popular_list(request, category_slug: str = None):
    """
    Список популярных товаров из определенной категории
    или со всех категорий
    """
    view_amount = 5  # кол-во отображаемых популярных товаров
    category = None
    page = request.GET.get('page')  # текущая страница из запроса

    products_ids = [int(pk) for pk in r.smembers('products_ids')]  # id всех товаров на сайте
    products_ids_sorted, products = get_products_sorted_by_views(products_ids)

    if category_slug:  # фильтр товаров по категории
        product_list = [
            products[pk] for pk in products_ids_sorted
            if category_slug == products[pk].category.slug
        ]
        category = Category.objects.get(slug=category_slug)
    else:
        product_list = [products[pk] for pk in products_ids_sorted]
    # пагинация списка товаров
    page_obj = get_page_obj(per_pages=2, page=page, queryset=product_list[:view_amount])
    products = page_obj.object_list

    sorting_by_price = SortByPriceForm()

    # сохранение id популярных товаров в redis
    r.hset('popular_prods', 'ids',
           ','.join(str(prod.pk) for prod in product_list))

    return render(request, 'goods/product/navs_categories_list.html', {'products': products,
                                                                       'page_obj': page_obj,
                                                                       'category': category,
                                                                       'sorting_by_price': sorting_by_price,
                                                                       'is_paginated': page_obj.has_other_pages(),
                                                                       'is_sorting': False,
                                                                       'place': 'popular'})


def product_ordering(request, place: str, category_slug: str = 'all', page: int = 1):
    """
    Сортировка товаров по цене, asc и desc
    """

    templates = {
        'mainlist': 'list.html',
        'popular': 'navs_categories_list.html',
        'new': 'navs_categories_list.html',
        'promotion': 'navs_categories_list.html',
    }

    products = None
    category = None
    sort = None
    product_ids_promotion = []

    product_ids_popular = (
        r.hget('popular_prods', 'ids').decode('utf-8').split(',') if place == 'popular' else []
    )
    product_ids_new = (
        r.hget('new_prods', 'ids').decode('utf-8').split(',') if place == 'new' else []
    )
    if place == 'promotion':
        lookup = Q(category__slug=category_slug, promotional=True) if category_slug != 'all' else Q(promotional=True)
        product_ids_promotion = [p.pk for p in Product.objects.filter(lookup)]

    sorting_by_price = SortByPriceForm()  # добавляем пустую форму на страницу после её подтверждения

    if request.method == 'GET':
        sort = request.GET.get('sort')

        if sort == 'p_asc' or sort == 'p_desc':
            asc_sort, desc_sort = ('promotional_price', 'price'), ('-promotional_price', '-price')
            if category_slug != 'all':  # если передана категория
                category = Category.objects.get(slug=category_slug)
                lookups = Q(category=category,
                            id__in=product_ids_popular or product_ids_new or product_ids_promotion,
                            _connector='OR')
                products = Product.objects.filter(lookups).order_by(*asc_sort if sort == 'p_asc' else desc_sort)
            else:
                lookups = Q(id__in=product_ids_popular or product_ids_new or product_ids_promotion or r.smembers(
                    'products_ids'))
                products = Product.objects.filter(lookups).order_by(*asc_sort if sort == 'p_asc' else desc_sort)
        else:
            lookups = Q(id__in=product_ids_popular or product_ids_new or product_ids_promotion or r.smembers(
                'products_ids'))
            products = Product.objects.filter(lookups)

    # пагинация
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)
    products = page_obj.object_list

    return render(request, f'goods/product/{templates[place]}', {'products': products,
                                                                 'category': category,
                                                                 'sorting_by_price': sorting_by_price,
                                                                 'selected_sort': sort,
                                                                 'page_obj': page_obj,
                                                                 'is_paginated': page_obj.has_other_pages(),
                                                                 'is_sorting': True,
                                                                 'place': place})


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
        product.rating = star
    else:  # расчет среднего рейтинга товара
        current_rating = round(((star + current_rating) / 2), 1)
        product.rating = current_rating
    product.save(update_fields=['rating'])  # сохранение в базе

    return JsonResponse({'success': True,
                         'current_rating': product.rating})
