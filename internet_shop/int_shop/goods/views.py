from decimal import Decimal

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, QuerySet, Case, When, Value
from django.http.response import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin

from account.models import Profile
from cart.forms import CartQuantityForm
from common.decorators import ajax_required, auth_profile_required
from common.moduls_init import redis
from common.utils import create_captcha_image
from goods.forms import (
    RatingSetForm,
    CommentProductForm,
    SortByPriceForm,
    SearchForm,
    FilterByManufacturerForm,
    FilterByPriceForm,
)
from goods.models import Product, Category, Favorite, Comment
from .filters import get_max_min_price
from .property_filters import get_property_for_category
from .utils import (
    distribute_properties_from_request,
    get_page_obj,
    get_collections_with_manufacturers_info,
    get_products_sorted_by_views
)


class ProductListView(ListView):
    """
    List of all products
    """
    model = Product
    template_name = 'goods/product/list.html'
    context_object_name = 'products'
    paginate_by = 8

    def __init__(self):
        """
        Overriding the method to add Profile instance, which is necessary
        for displaying info on the product card about whether product into favorite for this instance or not
        """
        super().__init__()
        self.profile = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = 'mainlist'
        if 'category_slug' in self.kwargs:  # if category has been got
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
            # updating manufacturer's queryset
            context['filter_manufacturers'].fields['manufacturer'].queryset = next(manufacturers_info)
            context['manufacturers_prod_qnty'] = next(manufacturers_info)  # products quantity for each manufacturer

        if self.request.user.is_authenticated:
            context['favorites'] = self.profile.profile_favorite.product.prefetch_related()

        context['sorting_by_price'] = SortByPriceForm()
        # show search request after receiving search results
        context['search_form'] = SearchForm(initial={'query': self.request.GET.get('query')})
        return context

    def get_queryset(self):
        if ('category_slug' and 'search_result') in self.kwargs:  # if category has been received and was search
            return self.kwargs.get('search_result')
        if 'category_slug' in self.kwargs:
            return super().get_queryset().filter(category__slug=self.kwargs['category_slug'])

        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        """
        Set to "profile" attribute guest or authenticated user
        """
        if request.user.is_authenticated:
            self.profile = Profile.objects.get(user=request.user)
        else:
            self.profile = Profile.objects.get(user__username='guest_user')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Method is using for the searching and simple loading main page
        """
        query = request.GET.get('query')
        category_slug = self.kwargs.get('category_slug')

        # if was search request
        if query:
            result = self._get_query_results(query, category_slug)
            self.kwargs['search_result'] = result

        return super().get(request, *args, **kwargs)

    @staticmethod
    def _get_query_results(query: str, category_slug: str = None) -> QuerySet:
        """
        Method is using for getting search request results
        """
        if category_slug:
            q = Q(category__slug=category_slug, similarity__gte=0.3)
        else:
            q = Q(similarity__gte=0.3)

        products = Product.available_objects.annotate(
            similarity=TrigramSimilarity('name', query), ).filter(q).order_by('-similarity')

        product_ids = [product.pk for product in products]
        # number of views of products found
        # compose "order_by" condition for sorting products by descending of the views
        product_views = [int(redis.hget(f'product_id:{pk}', 'views') or 0) for pk in product_ids]
        order_condition = Case(*[When(pk=pk, then=Value(views)) for pk, views in zip(product_ids, product_views)])
        result = Product.available_objects.filter(id__in=product_ids).order_by(-order_condition)
        return result


class ProductDetailView(DetailView, FormMixin):
    """
    Detail information about product
    """
    model = Product
    template_name = 'goods/product/detail.html'
    slug_url_kwarg = 'product_slug'
    pk_url_kwarg = 'product_pk'
    context_object_name = 'product'
    form_class = RatingSetForm  # form_class added from FormMixin

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None
        self.profile = None

    def get_success_url(self):
        """
        Returns URL for transition after handling valid form
        """
        return reverse('goods:product_detail', kwargs={'product_pk': self.kwargs['product_pk'],
                                                       'product_slug': self.kwargs['product_slug']})

    def dispatch(self, request, *args, **kwargs):
        """
        Set to "profile" attribute guest or authenticated user
        """
        if request.user.is_authenticated:
            self.profile = Profile.objects.get(user=request.user)
        else:
            self.profile = Profile.objects.get(user__username='guest_user')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['captcha_image'] = create_captcha_image(self.request, width=135, font_size=30)
        context['comment_form'] = CommentProductForm()
        context['quantity_form'] = CartQuantityForm()
        # getting all Profile objects, that commented on the current product and rated product comment
        context['comments'] = self.object.comments.prefetch_related('profile',
                                                                    'profiles_likes',
                                                                    'profiles_unlikes').order_by('-created')
        # getting all Property objects, that belongs to the current product
        context['properties'] = self.object.properties.select_related('category_property')
        # fill the name and email in the send comment form, if user is authenticated
        if self.request.user.is_authenticated:
            context['comment_form'].fields['user_name'].initial = self.request.user.first_name
            context['comment_form'].fields['user_email'].initial = self.request.user.email
            context['is_in_favorite'] = self.is_in_favorite()  # whether current product is in profile's favorite
            context['profile_rated_comments'] = self.get_profile_rated_comments()
        return context

    def is_in_favorite(self) -> bool:
        """
        Returns whether current product is in the current profile's favorite
        """
        # getting Favorite instance that linked to current Profile
        fav_obj = Favorite.objects.get(profile=self.profile)
        return self.object in fav_obj.product.prefetch_related()

    def get_profile_rated_comments(self) -> dict:
        """
        Returns ids of comments, under which current profile has set like or dislike
        """
        liked_comments = self.profile.comments_liked.all()
        unliked_comments = self.profile.comments_unliked.all()
        return {'liked_comments': [c.pk for c in liked_comments], 'unliked_comments': [c.pk for c in unliked_comments]}

    def post(self, request, *args, **kwargs):
        # if it's AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return self.set_like_dislike_comment(request)
        else:
            return self.send_comment_about_product()

    def send_comment_about_product(self):
        """
        Method returns invalid form with errors or redirect to the page
        with detail product under what that comment has been added successfully
        """
        self.object = self.get_object()
        form = self.get_form(form_class=CommentProductForm)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.product = self.object  # link the comment to the current product
            new_comment.profile = self.profile
            new_comment.save()  # save the comment to DB
            captcha_text = form.cleaned_data.get('captcha')
            # delete captcha text, when user has posted comment successfully
            redis.hdel(f'captcha:{captcha_text}', 'captcha_text')
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    @auth_profile_required
    def set_like_dislike_comment(self, request):
        """
        Method set like or dislike under comment
        """
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action')  # like/unlike
        comment = Comment.objects.get(pk=comment_id)

        liked_comments = self.profile.comments_liked.all()
        unliked_comments = self.profile.comments_unliked.all()

        # set like/dislike for the comment
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

    def form_invalid(self, form):
        """
        Overriding the method for adding CommentProductForm instance with errors to the context
        """
        context = self.get_context_data()
        context.update(comment_form=form)
        return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        """
        Method is using for increase number of views of the current product
        while transition to product detail page
        """
        object_pk = self.kwargs.get(self.pk_url_kwarg)  # getting product's id from URL kwargs
        # increment number of views by 1 while it's watched
        # add products to the set that profile has watched
        # set expire time for redis key i.e. deleting products ids from redis in 7 days, that user has watched
        redis.hincrby(f'product_id:{object_pk}', 'views', 1)
        redis.sadd(f'profile_id:{self.profile.pk}', object_pk)
        redis.expire(f'profile_id:{self.profile.pk}', time=604800, nx=True)
        return super().get(request, *args, **kwargs)


@auth_profile_required
@require_POST
@ajax_required
def add_or_remove_product_favorite(request) -> JsonResponse:
    """
    Adding or removing product to/from favorite
    """
    product_id = request.POST.get('product_id')
    action = request.POST.get('action')
    product = Product.available_objects.get(pk=product_id)

    profile = Profile.objects.get(user=request.user)

    if action == 'add':
        profile.profile_favorite.product.add(product)
    elif action == 'remove':
        profile.profile_favorite.product.remove(product)

    # products quantity in the favorite for current profile
    amount_prods = profile.profile_favorite.product.all().count()

    return JsonResponse({'success': True,
                         'amount_prods': amount_prods})


class FilterResultsView(ListView):
    """
    Displaying sample results after filter has been applied
    """
    model = Product
    template_name = 'goods/product/list.html'
    context_object_name = 'products'
    paginate_by = 3

    def __init__(self):
        super().__init__()
        self.filter_qs = None  # queryset with the products, received after filter

    @property
    def queryset_filter(self):
        return self.filter_qs

    @queryset_filter.setter
    def queryset_filter(self, qs):
        if isinstance(qs, QuerySet):
            self.filter_qs = qs

    def get(self, request, *args, **kwargs):
        if request.GET:  # if form with filter terms was submitted
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
        lookups = Q(category__slug=self.kwargs['category_slug'])

        # selection of products by price
        if 'filter_price' in self.kwargs:
            min_price = self.kwargs.get('filter_price')[0]
            max_price = self.kwargs.get('filter_price')[1]
            lookups &= Q(price__gte=min_price, price__lte=max_price)
        # selection of products by manufacturer
        if 'filter_manufacturers' in self.kwargs:
            manufacturers = self.kwargs.get('filter_manufacturers')
            lookups &= Q(manufacturer_id__in=manufacturers)
        # selection of products by properties
        if 'props' in self.kwargs:
            properties = self.kwargs.get('props')
            props_dict = distribute_properties_from_request(properties)
            lookups &= Q(properties__category_property__id__in=props_dict['ids'],
                         properties__name__in=props_dict['names'],
                         properties__text_value__in=props_dict['text_values'],
                         properties__numeric_value__in=props_dict['numeric_values'])

        # getting in the queryset only the unique results
        result_queryset = Product.available_objects.distinct().filter(lookups)

        self.queryset_filter = result_queryset  # save queryset to the class property
        return result_queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['place'] = 'filter_list'
        if 'category_slug' in self.kwargs:
            context['category'] = Category.objects.get(slug=self.kwargs.get('category_slug'))

            context['category_properties'] = get_property_for_category(context['category'].name, self.queryset_filter)

            if 'filter_price' in self.kwargs:
                min_price = Decimal(self.kwargs['filter_price'][0])
                max_price = Decimal(self.kwargs['filter_price'][1])
            else:
                max_price, min_price = get_max_min_price(category_slug=self.kwargs.get('category_slug'))

            context['filter_price'] = FilterByPriceForm(initial={
                'price_min': min_price,
                'price_max': max_price,
            })

            category_products = self.queryset_filter  # all products for the category, that were filtered
            manufacturers_info = get_collections_with_manufacturers_info(qs=category_products)

            # updating queryset and marking selected manufacturers
            context['filter_manufacturers'] = FilterByManufacturerForm(initial={
                'manufacturer': self.kwargs.get('filter_manufacturers')

            })
            context['filter_manufacturers'].fields['manufacturer'].queryset = next(manufacturers_info)
            context['manufacturers_prod_qnty'] = next(manufacturers_info)  # products quantity of each manufacturer
        context['sorting_by_price'] = SortByPriceForm()

        return context


def promotion_list(request, category_slug: str = None):
    """
    Promotions products list
    """
    category = Category.objects.get(slug=category_slug) if category_slug else ''
    lookup = Q(category__slug=category_slug, promotional=True) if category_slug else Q(promotional=True)
    products = Product.available_objects.filter(lookup)
    page = request.GET.get('page')  # getting current page from the request
    # list pagination
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)
    products = page_obj.object_list  # list of the products in the selected page
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
    Products list, that were added to the site 2 weeks ago and considered as new
    """
    category = Category.objects.get(slug=category_slug) if category_slug else ''
    now = timezone.now()
    diff = now - timezone.timedelta(weeks=2)  # calculate the difference
    lookup = Q(created__gt=diff, category__slug=category_slug) if category_slug else Q(created__gt=diff)

    products = Product.available_objects.filter(lookup)
    # saving ids of the new products to redis
    redis.hset('new_prods', 'ids', ','.join(str(prod.pk) for prod in products))
    page = request.GET.get('page')  # getting current page from the request
    page_obj = get_page_obj(per_pages=1, page=page, queryset=products)  # list pagination

    products = page_obj.object_list  # list of the products in the selected page
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
    List of the popular products from certain category or from all categories
    """
    view_amount = 5  # displaying number of popular products
    category = None
    page = request.GET.get('page')  # getting current page from the request

    products_ids = [int(pk) for pk in redis.smembers('products_ids')]  # ids of all products
    products_ids_sorted, products = get_products_sorted_by_views(products_ids)

    if category_slug:  # products filter by category
        product_list = [
            products[pk] for pk in products_ids_sorted
            if category_slug == products[pk].category.slug
        ]
        category = Category.objects.get(slug=category_slug)
    else:
        product_list = [products[pk] for pk in products_ids_sorted]
    # list pagintion
    page_obj = get_page_obj(per_pages=2, page=page, queryset=product_list[:view_amount])
    products = page_obj.object_list

    sorting_by_price = SortByPriceForm()

    # saving popular products ids to redis
    redis.hset('popular_prods', 'ids', ','.join(str(prod.pk) for prod in product_list))

    return render(request, 'goods/product/navs_categories_list.html', {'products': products,
                                                                       'page_obj': page_obj,
                                                                       'category': category,
                                                                       'sorting_by_price': sorting_by_price,
                                                                       'is_paginated': page_obj.has_other_pages(),
                                                                       'is_sorting': False,
                                                                       'place': 'popular'})


def product_ordering(request, place: str, category_slug: str = 'all', page: int = 1):
    """
    Sorting products by price
    """
    # names of templates, that will be rendering for each category (popular, new, promotion, main products list)
    templates = {
        'mainlist': 'list.html',
        'popular': 'navs_categories_list.html',
        'new': 'navs_categories_list.html',
        'promotion': 'navs_categories_list.html',
    }

    products = None
    category = None
    sort = None
    category_properties = None
    product_ids_promotion = []

    product_ids_popular = (
        redis.hget('popular_prods', 'ids').decode('utf-8').split(',') if place == 'popular' else []
    )
    product_ids_new = (
        redis.hget('new_prods', 'ids').decode('utf-8').split(',') if place == 'new' else []
    )
    if place == 'promotion':
        lookup = Q(category__slug=category_slug, promotional=True) if category_slug != 'all' else Q(promotional=True)
        product_ids_promotion = [p.pk for p in Product.available_objects.filter(lookup)]

    if request.method == 'GET':
        sort = request.GET.get('sort')
        # if sort is needed
        if sort == 'p_asc' or sort == 'p_desc':
            if category_slug != 'all':  # if category has been received
                category = Category.objects.get(slug=category_slug)
                lookups = Q(category=category,
                            id__in=product_ids_popular or product_ids_new or product_ids_promotion or redis.smembers(
                                'products_ids'))
                products = Product.available_objects.filter(lookups).annotate(sort_order=Case(
                    When(promotional=True, then='promotional_price'),
                    default='price')
                ).order_by('sort_order' if sort == 'p_asc' else '-sort_order')
            else:
                lookups = Q(id__in=product_ids_popular or product_ids_new or product_ids_promotion or redis.smembers(
                    'products_ids'))
                products = Product.available_objects.filter(lookups).annotate(sort_order=Case(
                    When(promotional=True, then='promotional_price'),
                    default='price')
                ).order_by('sort_order' if sort == 'p_asc' else '-sort_order')
        else:
            if category_slug != 'all':
                category = Category.objects.get(slug=category_slug)
                lookups = Q(category=category,
                            id__in=product_ids_popular or product_ids_new or product_ids_promotion or redis.smembers(
                                'products_ids'))
            else:
                lookups = Q(id__in=product_ids_popular or product_ids_new or product_ids_promotion or redis.smembers(
                    'products_ids'))

            products = Product.available_objects.filter(lookups)

    # list pagination
    page_obj = get_page_obj(per_pages=2, page=page, queryset=products)
    page_products = page_obj.object_list

    sorting_by_price = SortByPriceForm()  # add the form to the page after form has been submitted

    max_price, min_price = get_max_min_price(category_slug=category_slug)
    filter_price = FilterByPriceForm(initial={
        'price_min': min_price,
        'price_max': max_price
    })

    manufacturers_info = get_collections_with_manufacturers_info(qs=products)
    filter_manufacturers = FilterByManufacturerForm()
    # updating manufacturer's queryset
    filter_manufacturers.fields['manufacturer'].queryset = next(manufacturers_info)
    manufacturers_prod_qnty = next(manufacturers_info)  # products quantity for each manufacturer

    if category_slug != 'all':
        category_properties = get_property_for_category(category.name)

    return render(request, f'goods/product/{templates[place]}', {'products': page_products,
                                                                 'category': category,
                                                                 'sorting_by_price': sorting_by_price,
                                                                 'selected_sort': sort,
                                                                 'page_obj': page_obj,
                                                                 'is_paginated': page_obj.has_other_pages(),
                                                                 'is_sorting': True,
                                                                 'place': place,
                                                                 'filter_price': filter_price,
                                                                 'filter_manufacturers': filter_manufacturers,
                                                                 'manufacturers_prod_qnty': manufacturers_prod_qnty,
                                                                 'category_properties': category_properties})


@require_POST
@ajax_required
def set_product_rating(request) -> JsonResponse:
    """
    Function set product rating using AJAX request
    """
    star = Decimal(request.POST.get('star'))  # rating, that user has installed (1 - 5)
    product_id = request.POST.get('product_id')
    product = Product.available_objects.get(pk=product_id)
    current_rating = product.rating
    if not current_rating:
        product.rating = f'{star:.1f}'
    else:  # evaluating average product rating
        current_rating = round(((star + current_rating) / 2), 1)
        product.rating = current_rating
    product.save(update_fields=['rating'])  # save to DB

    return JsonResponse({'success': True,
                         'current_rating': product.rating})
