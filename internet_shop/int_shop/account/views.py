import redis as redis
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.generic import CreateView
from django.conf import settings

from goods.models import Product, Favorite
from orders.models import OrderItem, Order
from .forms import LoginForm, UserPasswordChangeForm, RegisterUserForm
from django.urls import reverse_lazy
from account.models import Profile
from .tasks import activate_account
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .tokens import activation_account_token
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import DetailView
from django.db.models import QuerySet
from datetime import datetime
from django.core import files
from .utils import get_image_from_url
import requests

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
            domain = get_current_site(request).domain
            is_secure = request.is_secure()
            # передача задачи по отправке письма в celery
            activate_account.delay({'domain': domain, 'is_secure': is_secure}, new_user.pk, new_user.email)
            # Создаем профиль пользователя с доп. полями
            Profile.objects.create(user=new_user,
                                   date_of_birth=date_of_birth,
                                   photo=user_photo,
                                   gender=form.cleaned_data.get('gender'))
            messages.success(request, 'Thank for your registration. Now you can login your account')
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
        context['favorites'] = self.object.profile_favorite.product.prefetch_related()

        # заказы и отдельные единицы для каждого заказа текущего пользователя self.object
        context['orders'] = Order.objects.select_related('profile', 'delivery').filter(profile_id=self.object.pk)
        context['order_items'] = {
            order.pk: OrderItem.objects.select_related('order', 'product').filter(order_id=order.pk)
            for order in context['orders']
        }

        coupons = self.object.coupons.prefetch_related().order_by('pk')
        # установка заказов для каждого купона self.object и возврат обновленного queryset coupons
        context['coupons'] = self._set_orders_for_coupon(context['orders'], coupons)

        context['comments'] = self.object.profile_comments.select_related('product').order_by('updated', 'created')
        context['present_cards'] = self.object.profile_cards.all()
        # товары, просмотренные пользователем self.object
        products_ids = (int(pk) for pk in r.smembers(f'profile_id:{self.object.pk}'))
        context['watched'] = Product.objects.filter(pk__in=products_ids)
        context['location'] = self.kwargs.get('location')

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
        for order in orders.order_by('coupon_id'):
            orders_for_coupon.setdefault(order.coupon, []).append(order)

        for coupon in coupons:
            for c, o in orders_for_coupon.items():
                # если существует купон для заказа и купоны одинаковы
                if c and c == coupon:
                    coupon.choices = o

        return coupons


def save_social_user_to_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'facebook':
        # если профиль еще не был создан
        if kwargs.get('is_new'):
            date_of_birth = response.get('birthday')
            gender = response.get('gender')[0].upper()
            photo_url = response.get('picture')['data']['url']
            photo_name = f'fb_{response.get("id")}_photo.jpeg'

            bytes_inst = get_image_from_url(photo_url)  # получение фото в байт-формате

            profile = Profile.objects.create(user_id=user.pk,
                                             gender=gender,
                                             date_of_birth=datetime.strptime(date_of_birth, '%m/%d/%Y'))

            profile.photo.save(photo_name, files.File(bytes_inst))  # сохранение фото для профиля

            Favorite.objects.create(profile=profile)  # создание объекта избранного для нового профиля

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
            date_of_birth = json_info['birthdays'][0]['date']
            account_id = json_info['resourceName'].split('/')[1]
            photo_name = f'google_{account_id}_photo.jpeg'

            profile = Profile.objects.create(user_id=user.pk,
                                             gender=gender[0],
                                             date_of_birth=datetime.strptime(
                                                 '/'.join(str(date_of_birth[k]) for k in date_of_birth), '%Y/%m/%d')
                                             )
            profile.photo.save(photo_name, files.File(bytes_inst))  # сохранение фото для профиля

            Favorite.objects.create(profile=profile)  # создание объекта избранного для нового профиля
