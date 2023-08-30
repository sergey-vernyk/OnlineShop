from datetime import datetime

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView
)
from django.contrib.messages.views import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView
from django.views.generic.edit import FormMixin

from account.models import Profile
from common.moduls_init import redis
from common.utils import create_captcha_image
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
from .tasks import activate_account
from .tokens import activation_account_token
from .utils import get_image_from_url, create_profile_from_social


class LoginUserView(LoginView):
    """
    Class for login user to the system
    """
    form_class = LoginForm

    def form_valid(self, form):
        # if check mark "remember me" is active - don't log out, until a browser is closed
        # it working not always correct in several browsers
        if form.cleaned_data.get('remember'):
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1200)  # otherwise log out in 20 minutes
        self.request.session.modified = True
        return super().form_valid(form)


class UserPasswordChangeView(PasswordChangeView):
    """
    Changing user account password view
    """
    form_class = UserPasswordChangeForm


class UserRegisterView(CreateView):
    """
    Registration user in the system view
    """
    form_class = RegisterUserForm
    template_name = 'registration/user_register_form.html'
    success_url = reverse_lazy('login')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['captcha_image'] = create_captcha_image(self.request)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            new_user = form.save(commit=False)  # creating user, but not save it
            date_of_birth = form.cleaned_data.get('date_of_birth')
            user_photo = form.cleaned_data.get('user_photo')
            # filling user's fields from form data
            new_user.username = form.cleaned_data.get('username')
            new_user.email = form.cleaned_data.get('email')
            new_user.first_name = form.cleaned_data.get('first_name')
            new_user.last_name = form.cleaned_data.get('last_name')
            new_user.is_active = False  # user not active
            new_user.save()  # save user to db
            # get domain and connection type for email body
            # for sending email to user's post for account activation
            domain = request.site.domain
            is_secure = request.is_secure()
            # passing sending email task to celery
            activate_account.delay({'domain': domain, 'is_secure': is_secure}, new_user.pk, new_user.email)
            # creating profile with additional fields
            profile = Profile.objects.create(user=new_user,
                                             date_of_birth=date_of_birth,
                                             photo=user_photo,
                                             gender=form.cleaned_data.get('gender'))
            Favorite.objects.create(profile=profile)  # creating favorite instance for profile
            messages.success(request, 'Please, check your email! '
                                      'You have to receive email with instruction for activate account')
            # delete captcha text, when user has complete registration
            redis.hdel(f'captcha:{form.cleaned_data.get("captcha")}', 'captcha_text')
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


def activate_user_account(request, uidb64, token):
    """
    Activation registered user account after sending to user
    email with activation link
    """
    try:
        # decoding user id from uidb64
        # and getting user from db
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, ObjectDoesNotExist):
        user = None
    # if user is exists and token term isn't end (token is valid)
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
    Detail information about user: his/her orders, personal info,
    favorite list etc.
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
        # composing coupons ids, which were used in profile's orders
        orders_id_with_coupons = [order.coupon.pk for order in context['orders'] if order.coupon]
        coupons = Coupon.objects.select_related('category').filter(id__in=orders_id_with_coupons).order_by('pk')
        # assignment orders for each profile coupon and return updated coupons queryset
        context['coupons'] = self._set_orders_for_coupon(context['orders'], coupons)
        context['comments'] = self.object.profile_comments.prefetch_related('product',
                                                                            'profiles_likes',
                                                                            'profiles_unlikes'
                                                                            ).order_by('-updated', '-created')
        if location == 'present_cards':
            context['present_cards'] = self.object.profile_cards.select_related('category', 'order')
        elif location == 'watched':
            # products viewed by profile
            products_ids = (int(pk) for pk in redis.smembers(f'profile_id:{self.object.pk}'))
            context['watched'] = Product.objects.filter(pk__in=products_ids)

        return context

    def get_object(self, queryset=None):
        """
        Return profile object by passed name in URL
        """
        return Profile.objects.get(user__username=self.kwargs.get('customer'))

    def _set_orders_for_coupon(self, orders: QuerySet, coupons: QuerySet) -> QuerySet:
        """
        Method sets order list for each profile's coupon, in which it was applied.
        Returns updated coupons queryset
        """
        orders_for_coupon = {}  # dictionary type {coupon: [order_1, order_2]}
        for order in orders:
            orders_for_coupon.setdefault(order.coupon, []).append(order)

        for coupon in coupons:
            for c, o in orders_for_coupon.items():
                # if order coupon is exists and coupons are equivalent
                if c and c == coupon:
                    coupon.choices = sorted(o, key=lambda y: y.pk)  # sort list ascending by order id
                    break

        return coupons


def save_social_user_to_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'facebook':
        # if profile wasn't be created
        if kwargs.get('is_new'):
            date_of_birth = datetime.strptime(response.get('birthday'), '%m/%d/%Y')
            gender = response.get('gender')[0].upper()
            photo_url = response.get('picture')['data']['url']
            photo_name = f'fb_{response.get("id")}_photo.jpeg'

            bytes_inst = get_image_from_url(photo_url)  # get photo in bytes format
            # creating profile from received data
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

            bytes_inst = get_image_from_url(photo_url)  # get photo in bytes format

            # headers for API request
            headers = {
                "Authorization": f"{token_type} {access_token}",
                "Accept": "application/json"
            }

            # getting user information from API (gender and birthdate)
            user_info = requests.get(
                url=(f'https://people.googleapis.com/v1/people/'
                     f'me?personFields=genders%2Cbirthdays&key={settings.API_KEY_GOOGLE}'),
                headers=headers)

            json_info = user_info.json()

            gender = date_of_birth = ''
            if 'genders' in json_info:
                gender = json_info['genders'][0]['formattedValue']
            if 'birthdays' in json_info:
                bd = json_info['birthdays'][0]['date']
                date_of_birth = datetime.strptime(
                    '/'.join(str(bd[k]) for k in bd), '%Y/%m/%d'
                )

            account_id = response['sub']
            photo_name = f'google_{account_id}_photo.jpeg'

            # creating profile from received data
            create_profile_from_social(date_of_birth=date_of_birth,
                                       gender=gender[0],
                                       user_id=user.pk,
                                       photo_name=photo_name,
                                       photo=bytes_inst)


class ForgotPasswordView(PasswordResetView):
    """
    View for sending email needed for reset forgotten password from account
    """

    form_class = ForgotPasswordForm
    template_name = 'registration/password_reset_form.html'
    success_url = reverse_lazy('password_reset')
    html_email_template_name = 'registration/password_reset_email_html.html'
    message = ("We've emailed you instructions for setting your password. "
               "If you don't receive an email, please make sure you've entered the address you registered with")

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['captcha_image'] = create_captcha_image(self.request, width=135, font_size=30)
        return context

    def form_valid(self, form):
        if form.is_valid():
            captcha_text = form.cleaned_data.get('captcha')
            # delete captcha text, when user has complete send email to the server
            redis.hdel(f'captcha:{captcha_text}', 'captcha_text')
            messages.success(self.request, mark_safe(self.message))  # displaying message to frontend

        return super().form_valid(form)


class SetNewPasswordView(PasswordResetConfirmView):
    """
    View for set new password after reset
    """
    form_class = SetNewPasswordForm
