from django.contrib import admin

from account.models import Profile
from goods.models import Favorite, Comment
from django.utils.html import mark_safe

from orders.models import Order
from present_cards.models import PresentCard


class PresentCardInline(admin.StackedInline):
    model = PresentCard
    extra = 0
    readonly_fields = ('valid_from', 'valid_to', 'category', 'code', 'amount')
    fieldsets = (
        ('PresentCards', {
            'classes': ('collapse',),
            'fields': ('code', 'valid_from', 'valid_to',
                       'from_name', 'from_email',
                       'category', 'message', 'amount'),
        }),
    )


class OrdersInline(admin.StackedInline):
    model = Order
    extra = 0
    fields = ('pay_method', 'is_paid', 'present_card', 'coupon', 'delivery', 'stripe_id', 'created', 'updated')
    readonly_fields = ('stripe_id', 'created', 'updated')


class FavoriteInline(admin.StackedInline):
    """
    Отображение избранных товаров
    в профиле пользователя
    """
    model = Favorite
    filter_horizontal = ('product',)  # поиск по добавленным товарам пользователя
    fieldsets = (
        ('Favorite', {
            'classes': ('collapse',),
            'fields': ('product', 'profile'),
        }),
    )


class CommentInline(admin.StackedInline):
    """
    Отображение комментариев к товару
    в профиле пользователя
    """
    model = Comment
    extra = 1
    readonly_fields = ('user_name', 'user_email', 'product', 'get_amount_profile_likes', 'get_amount_profile_unlikes')
    fieldsets = (
        ('Comment', {
            'classes': ('collapse',),
            'fields': ('user_name', 'user_email', 'body',
                       'get_amount_profile_likes', 'get_amount_profile_unlikes', 'product'),
        }),
    )

    @admin.display(description='Likes')
    def get_amount_profile_likes(self, obj):
        """
        Возвращает кол-во лайков под комментарием obj
        """
        return obj.profiles_likes.count()

    @admin.display(description='Unlikes')
    def get_amount_profile_unlikes(self, obj):
        """
        Возвращает кол-во дизлайков под комментарием obj
        """
        return obj.profiles_unlikes.count()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Профиль пользователя
    """
    list_display = ['user', 'gender', 'email_confirm']
    fields = ('profile_full_name', 'user', 'date_of_birth',
              'profile_photo_tag', 'photo', 'phone_number', 'created',
              'about', 'coupons')
    inlines = [FavoriteInline, CommentInline, PresentCardInline, OrdersInline]
    readonly_fields = ['profile_photo_tag', 'created', 'profile_full_name']
    filter_horizontal = ('coupons',)

    @admin.display(description='Username')  # отображение названия поля в шапке админ сайта модели
    def profile_full_name(self, obj):
        """
        Добавление имени и фамилии пользователя из встроенной модели
        в модель профиля
        """
        return f'{obj.user.first_name} {obj.user.last_name}'

    @admin.display(description='Photo')
    def profile_photo_tag(self, obj):
        """
        Фото профиля пользователя
        """
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="100" height="100"/>')
