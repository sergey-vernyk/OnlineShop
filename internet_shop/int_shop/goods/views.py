import redis
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from django.conf import settings
from account.models import Profile
from django.views.decorators.http import require_POST
from django.http.response import JsonResponse
from goods.forms import RatingSetForm, CommentProductForm, SortByPriceForm, SearchForm
from cart.forms import CartQuantityForm
from goods.logic import distribute_properties_from_request, get_page_obj
from goods.models import Product, Category, Favorite, Comment
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .utils import GoodsContextMixin
from common.decorators import ajax_required
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

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
    paginate_by = 2

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
        if 'category_slug' in self.kwargs:  # если передана категория
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))
            context = self.add_to_context(context, self.kwargs)

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

    def get(self, request, *args, **kwargs):
        """
        Метод используется для поиска по сайту
        и для обычной загрузки главной страницы сайта
        """
        if request.user.is_authenticated:
            self.profile = Profile.objects.get(user=self.request.user)  # получение текущего профиля
        else:
            self.profile = Profile.objects.get(user__username='guest_user')

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
        self.profile = None

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

    def post(self, request, *args, **kwargs):
        # если AJAX запрос
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            comment_id = request.POST.get('comment_id')
            action = request.POST.get('action')  # like/unlike
            comment = Comment.objects.get(pk=comment_id)
            profile = Profile.objects.get(user=request.user)
            liked_comments = profile.comments_liked.all()
            unliked_comments = profile.comments_unliked.all()

            # установка like/dislike для комментария
            if action == 'like':
                if comment in liked_comments:
                    comment.profiles_likes.remove(profile)
                else:
                    comment.profiles_likes.add(profile)
                    comment.profiles_unlikes.remove(profile)

            elif action == 'unlike':
                if comment in unliked_comments:
                    comment.profiles_unlikes.remove(profile)
                else:
                    comment.profiles_unlikes.add(profile)
                    comment.profiles_likes.remove(profile)

            new_count_likes = comment.profiles_likes.count()
            new_count_unlikes = comment.profiles_unlikes.count()
            return JsonResponse({'success': True,
                                 'new_count_likes': new_count_likes,
                                 'new_count_unlikes': new_count_unlikes})
        else:
            self.object = self.get_object()
        #  если пользователь аутентифицирован на сайте и отправляет комментарий
        if 'comment_sent' in request.POST:
            # присвоить объект представлению
            form = self.get_form(form_class=CommentProductForm)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.product = self.object  # привязка комментария к текущему товару
                # привязка комментария к текущему профилю или гостевому аккаунту
                profile_instance = guest_user = None
                if request.user.is_authenticated:
                    profile_instance = Profile.objects.get(user=request.user)
                else:
                    guest_user = Profile.objects.get(user__username='guest_user')

                new_comment.profile = profile_instance or guest_user
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
        object_pk = self.kwargs.get(self.pk_url_kwarg)  # получение id товара из аргументов URL
        if request.user.is_authenticated:
            self.profile = Profile.objects.get(user=request.user)
            # увеличение кол-ва просмотров товара на 1 при его просмотре
            r.hincrby(f'product_id:{object_pk}', 'views', 1)
            # добавление товара в множество просмотренных товаров пользователем с profile_id
            r.sadd(f'profile_id:{self.profile.pk}', object_pk)
        else:
            self.profile = Profile.objects.get(user__username='guest_user')
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


def promotion_list(request, category_slug: str = None):
    """
    Список товаров, которые отмечены как акционные
    """
    category_name = Category.objects.get(slug=category_slug) if category_slug else ''
    lookup = Q(category__slug=category_slug, promotional=True) if category_slug else Q(promotional=True)
    products = Product.objects.filter(lookup)
    page = request.GET.get('page')  # получаем текущую страницу из запроса
    # пагинация списка
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)
    products = page_obj.object_list  # список товаров на выбранной странице
    sorting_by_price = SortByPriceForm()

    return render(request, 'goods/product/promotion_list.html', {'products': products,
                                                                 'page_obj': page_obj,
                                                                 'category_name': category_name,
                                                                 'sorting_by_price': sorting_by_price,
                                                                 'is_paginated': page_obj.has_other_pages(),
                                                                 'is_sorting': False})


def new_list(request, category_slug: str = None):
    """
    Список товаров, которые добавлены на сайт
    2 недели назад и считаются новыми
    """
    category_name = Category.objects.get(slug=category_slug) if category_slug else ''
    now = timezone.now()
    diff = now - timezone.timedelta(weeks=2)
    lookup = Q(created__gt=diff, category__slug=category_slug) if category_slug else Q(created__gt=diff)

    products = Product.objects.filter(lookup)
    r.hset('new_prods', 'ids', ','.join(str(prod.pk) for prod in products))  # сохранение id новых товаров в redis
    page = request.GET.get('page')  # получаем текущую страницу из запроса
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)

    products = page_obj.object_list  # список товаров на выбранной странице
    sorting_by_price = SortByPriceForm()

    return render(request, 'goods/product/new_list.html', {'products': products,
                                                           'page_obj': page_obj,
                                                           'category_name': category_name,
                                                           'sorting_by_price': sorting_by_price,
                                                           'is_paginated': page_obj.has_other_pages(),
                                                           'is_sorting': False})


def popular_list(request, category_slug: str = None):  # TODO refactoring
    """
    Список популярных товаров из категории category_slug
    или список таких товаров со всех категорий на сайте
    """
    view_amount = 5  # кол-во отображаемых популярных товаров
    category_name = ''
    page = request.GET.get('page')  # получаем текущую страницу из запроса

    products_ids = [int(pk) for pk in r.smembers('products_ids')]  # id всех товаров на сайте

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
    page_obj = get_page_obj(per_pages=2, page=page, queryset=product_list[:view_amount])
    products = page_obj.object_list

    sorting_by_price = SortByPriceForm()

    # сохранение id популярных товаров в redis
    r.hset('popular_prods', 'ids',
           ','.join(str(prod.pk) for prod in product_list[:view_amount]))

    return render(request, 'goods/product/popular_list.html', {'products': products,
                                                               'page_obj': page_obj,
                                                               'category_name': category_name,
                                                               'sorting_by_price': sorting_by_price,
                                                               'is_paginated': page_obj.has_other_pages(),
                                                               'is_sorting': False})


def product_ordering(request, place: str, category_slug: str = 'all', page: int = 1):
    """
    Сортировка товаров по цене, asc и desc
    """

    templates = {
        'mainlist': 'list.html',
        'popular': 'popular_list.html',
        'new': 'new_list.html',
        'promotion': 'promotion_list.html',
    }

    products = None
    category = None
    sort = None
    product_ids_popular = (
        r.hget('popular_prods', 'ids').decode('utf-8').split(',') if place == 'popular' else []
    )
    product_ids_new = (
        r.hget('new_prods', 'ids').decode('utf-8').split(',') if place == 'new' else []
    )

    sorting_by_price = SortByPriceForm()  # добавляем пустую форму на страницу после её подтверждения

    if request.method == 'GET':
        sort = request.GET.get('sort')

        if sort == 'p_asc' or sort == 'p_desc':
            if category_slug != 'all':  # если передана категория
                category = Category.objects.get(slug=category_slug)
                lookups = Q(category=category, id__in=product_ids_popular or product_ids_new, _connector='OR')
                products = Product.objects.filter(lookups).order_by('price' if sort == 'p_asc' else '-price')
            else:
                lookups = Q(id__in=product_ids_popular or product_ids_new or r.smembers('products_ids'))
                products = Product.objects.filter(lookups).order_by('price' if sort == 'p_asc' else '-price')

        else:
            lookups = Q(id__in=product_ids_popular or product_ids_new or r.smembers('products_ids'))
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
                                                                 'is_sorting': True})


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
