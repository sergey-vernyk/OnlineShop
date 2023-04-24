from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.generic import CreateView

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

        context['comments'] = self.object.profile_comments.all()
        context['present_cards'] = self.object.profile_cards.all()
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
                # если существует купон под заказ и купоны одинаковы
                if c and c == coupon:
                    coupon.choices = o

        return coupons
