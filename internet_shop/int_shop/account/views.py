import redis as redis
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView
)
from django.views.generic import CreateView
from django.conf import settings

from coupons.models import Coupon
from goods.models import Product, Favorite
from orders.models import Order
from .forms import (
    LoginForm,
    UserPasswordChangeForm,
    RegisterUserForm,
    ForgotPasswordForm,
    SetNewPasswordForm
)
from django.urls import reverse_lazy
from account.models import Profile
from .tasks import activate_account
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .tokens import activation_account_token
from django.shortcuts import redirect
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import DetailView
from django.db.models import QuerySet
from datetime import datetime
from .utils import get_image_from_url, create_profile_from_social
import requests
from django.views.generic.edit import FormMixin
from django.contrib.messages.views import messages
from django.utils.safestring import mark_safe

# инициализация Redis
r = redis.Redis(host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB)


class LoginUserView(LoginView):
    """
    Представление входа пользователя
    """
    form_class = LoginForm

    def form_valid(self, form):
        # если активна галочка "запомнить меня" - не выходить с системы до закрытия браузера
        # работает не всегда корректно в некоторых браузерах
        if form.cleaned_data.get('remember'):
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1200)  # иначе выйти с системы через 20 минут
        self.request.session.modified = True
        return super().form_valid(form)


class UserPasswordChangeView(PasswordChangeView):
    """
    Представление для изменения пароля
    пользовательского аккаунта
    """
    form_class = UserPasswordChangeForm


class UserRegisterView(CreateView):
    """
    Представление для регистрации пользователя в системе
    """
    form_class = RegisterUserForm
    template_name = 'registration/user_register_form.html'
    success_url = reverse_lazy('login')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            new_user = form.save(commit=False)  # создаем пользователя, но в базе не сохраняем
            date_of_birth = form.cleaned_data.get('date_of_birth')
            user_photo = form.cleaned_data.get('user_photo')
            # заполняем поля пользователя с данных формы
            new_user.username = form.cleaned_data.get('username')
            new_user.email = form.cleaned_data.get('email')
            new_user.first_name = form.cleaned_data.get('first_name')
            new_user.last_name = form.cleaned_data.get('last_name')
            new_user.is_active = False  # пользователь не активен
            new_user.save()  # сохраняем пользователя в базе
            # получаем домен и тип соединения для тела email
            # для отправки на почту пользователю для активации аккаунта
            domain = request.site.domain
            is_secure = request.is_secure()
            # передача задачи по отправке письма в celery
            activate_account.delay({'domain': domain, 'is_secure': is_secure}, new_user.pk, new_user.email)
            # Создаем профиль пользователя с доп. полями
            profile = Profile.objects.create(user=new_user,
                                             date_of_birth=date_of_birth,
                                             photo=user_photo,
                                             gender=form.cleaned_data.get('gender'))
            Favorite.objects.create(profile=profile)  # создание объекта избранного для профиля
            messages.success(request, f'Please, check your email! '
                                      f'You have to receive email with instruction for activate account')
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def activate_user_account(request, uidb64, token):
    """
    Активация аккаунта зарегистрированного пользователя
    после отправки этому пользователю email сообщения
    со ссылкой для активации
    """
    try:
        # декодирование id пользователя с uid64
        # и получения пользователя из БД с данным id
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, ObjectDoesNotExist):
        user = None
    # если есть пользователь и время жизни токена не закончилось (токен валидный)
    if user is not None and activation_account_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        profile = Profile.objects.get(user=user)
        profile.email_confirm = True
        profile.save(update_fields=['email_confirm'])
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('goods:product_list')


class DetailUserView(DetailView):
    """
    Представление для отображения детальной информации
    о пользователе: его заказы, информация, список избранных товаров и т.д.
    """
    model = Profile
    context_object_name = 'customer'
    template_name = 'account/user/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location'] = location = self.kwargs.get('location')

        context['favorites'] = self.object.profile_favorite.product.prefetch_related('comments')
        context['orders'] = Order.objects.prefetch_related('delivery',
                                                           'coupon',
                                                           'present_card',
                                                           'items',
                                                           'items__product').filter(profile=self.object)
        # формирование id купонов, которые были использованы в заказах пользователя profile
        orders_id_with_coupons = [order.coupon.pk for order in context['orders'] if order.coupon]
        coupons = Coupon.objects.select_related('category').filter(id__in=orders_id_with_coupons).order_by('pk')
        # установка заказов для каждого купона self.object и возврат обновленного queryset coupons
        context['coupons'] = self._set_orders_for_coupon(context['orders'], coupons)
        context['comments'] = self.object.profile_comments.prefetch_related('product',
                                                                            'profiles_likes',
                                                                            'profiles_unlikes'
                                                                            ).order_by('-updated', '-created')
        if location == 'present_cards':
            context['present_cards'] = self.object.profile_cards.select_related('category', 'order')
        elif location == 'watched':
            # товары, просмотренные пользователем self.object
            products_ids = (int(pk) for pk in r.smembers(f'profile_id:{self.object.pk}'))
            context['watched'] = Product.objects.filter(pk__in=products_ids)

        return context

    def get_object(self, queryset=None):
        """
        Возвращает объект пользователя по переданному
        имени в URLconf
        """
        return Profile.objects.get(user__username=self.kwargs.get('customer'))

    def _set_orders_for_coupon(self, orders: QuerySet, coupons: QuerySet) -> QuerySet:
        """
        Метод устанавливает в каждом купоне профиля список заказов,
        в которых был применен этот купон и возвращает обновленный queryset coupons
        """

        orders_for_coupon = {}  # словарь типа {купон: [заказ_1, заказ_2]}
        for order in orders:
            orders_for_coupon.setdefault(order.coupon, []).append(order)

        for coupon in coupons:
            for c, o in orders_for_coupon.items():
                # если существует купон для заказа и купоны одинаковы
                if c and c == coupon:
                    coupon.choices = sorted(o, key=lambda y: y.pk)  # сортировка списка по возрастанию id заказов
                    break

        return coupons


def save_social_user_to_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'facebook':
        # если профиль еще не был создан
        if kwargs.get('is_new'):
            date_of_birth = datetime.strptime(response.get('birthday'), '%m/%d/%Y')
            gender = response.get('gender')[0].upper()
            photo_url = response.get('picture')['data']['url']
            photo_name = f'fb_{response.get("id")}_photo.jpeg'

            bytes_inst = get_image_from_url(photo_url)  # получение фото в байт-формате
            # создание профиля с полученных данных
            create_profile_from_social(date_of_birth=date_of_birth,
                                       gender=gender,
                                       user_id=user.pk,
                                       photo_name=photo_name,
                                       photo=bytes_inst)

    elif backend.name == 'google-oauth2':
        if kwargs.get('is_new'):
            photo_url = response.get('picture')
            token_type = response.get('token_type')
            access_token = response.get('access_token')

            bytes_inst = get_image_from_url(photo_url)  # получение фото в байт-формате

            # headers для запроса api
            headers = {
                "Authorization": f"{token_type} {access_token}",
                "Accept": "application/json"
            }

            # получение информации пользователя с api (пол и дата рождения)
            user_info = requests.get(
                url=('https://people.googleapis.com/v1/people/'
                     'me?personFields=genders%2Cbirthdays&key=AIzaSyDGwpM8rcsPoUZMMplrsU1BTGq-90wZbik'),
                headers=headers)

            json_info = user_info.json()

            gender = json_info['genders'][0]['formattedValue']
            bd = json_info['birthdays'][0]['date']
            date_of_birth = datetime.strptime(
                '/'.join(str(bd[k]) for k in bd), '%Y/%m/%d'
            )
            account_id = json_info['resourceName'].split('/')[1]
            photo_name = f'google_{account_id}_photo.jpeg'

            # создание профиля с полученных данных
            create_profile_from_social(date_of_birth=date_of_birth,
                                       gender=gender[0],
                                       user_id=user.pk,
                                       photo_name=photo_name,
                                       photo=bytes_inst)


class ForgotPasswordView(PasswordResetView, FormMixin):
    """
    Представления для отправки Email для сброса забытого пароля
    от учетной записи
    """

    form_class = ForgotPasswordForm
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset')
    html_email_template_name = 'registration/password_reset_email_html.html'
    message = (f"We've emailed you instructions for setting your password. "
               f"If you don't receive an email, please make sure you've entered the address you registered with")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            messages.success(request, mark_safe(self.message))  # вывод сообщения внизу формы

        return super().post(request, *args, **kwargs)


class SetNewPasswordView(PasswordResetConfirmView):
    """
    Представление для установки нового пароля после сброса
    """
    form_class = SetNewPasswordForm
