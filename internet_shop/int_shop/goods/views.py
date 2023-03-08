from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin

from account.models import Profile
from goods.forms import RatingSetForm, CommentProductForm
from cart.forms import CartQuantityForm
from goods.models import Product, Category, Favorite
from django.urls import reverse
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist


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


class ProductDetailView(FormMixin, DetailView):
    """
    Подробное описание товара
    """
    model = Product
    template_name = 'goods/product/detail.html'
    slug_url_kwarg = 'product_slug'
    pk_url_kwarg = 'product_pk'
    form_class = RatingSetForm  # форма добавляется из FormMixin

    def get_success_url(self):
        """
        Возвращает URL для перехода после обработки валидной формы
        """
        return reverse('goods:product_detail', kwargs={'product_pk': self.kwargs['product_pk'],
                                                       'product_slug': self.kwargs['product_slug']})

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['rating_form'] = self.form_class  # добавляем форму рейтинга в контекст
        context['comment_form'] = CommentProductForm()  # добавляем форму комментария в контекст
        context['quantity_form'] = CartQuantityForm()  # добавляем форму кол-ва товаров в контекст
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
        # если был поставлен рейтинг
        elif 'rating_sent' in request.POST:
            form = self.get_form(form_class=RatingSetForm)
            if form.is_valid():
                current_rating = self.object.rating
                rating = form.cleaned_data.get('star')
                if not current_rating:
                    self.object.rating = Decimal(rating)
                else:  # расчет среднего рейтинга товара
                    self.object.rating = round((rating + current_rating) / 2, 1)
                self.object.save()  # сохранение в базе
                return self.form_valid(form)
            else:
                return self.form_invalid(form)


class FavoriteListView(ListView):
    """
    Представление для отображения избранных товаров
    конкретного пользователя
    """
    template_name = 'account/user/favorite_products.html'

    def get_queryset(self):
        """
        Возвращает товары, которые текущий пользователь
        добавил в избранное.
        'username' передается в URL
        """
        return Profile.objects.get(user__username=self.kwargs['username']).profile_favorite.product.prefetch_related()

    def get_context_data(self, *, object_list=None, **kwargs):
        """
        Добавляет в контекст текущего пользователя
        """
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


@login_required()
def add_or_remove_product_favorite(request, product_pk: int, action: str) -> redirect:
    """
    Добавление товара в избранное или удаление его
    """
    product = Product.objects.get(pk=product_pk)
    profile = Profile.objects.get(user=request.user)

    if action == 'add':
        Favorite.objects.get(profile=profile).product.add(product)
    elif action == 'remove':
        Favorite.objects.get(profile=profile).product.remove(product)

    return redirect(reverse('goods:user_product_favorites_list', args=(request.user.username,)))
