from django.contrib import admin
from django.utils.html import mark_safe

from account.models import Profile
from goods.models import Favorite, Comment
from orders.models import Order
from present_cards.models import PresentCard


class PresentCardInline(admin.StackedInline):
    """
    Displaying profile's present cards inline
    """
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
    """
    Displaying profile's orders inline
    """
    model = Order
    extra = 0
    fields = ('pay_method', 'is_paid', 'present_card', 'coupon', 'delivery', 'stripe_id', 'created', 'updated')
    readonly_fields = ('stripe_id', 'created', 'updated')


class FavoriteInline(admin.StackedInline):
    """
    Displaying favorite products in user's profile
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
    Displaying product's comments in user profile
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
        Returns likes count under comment obj
        """
        return obj.profiles_likes.count()

    @admin.display(description='Unlikes')
    def get_amount_profile_unlikes(self, obj):
        """
        Returns dislikes count under comment obj
        """
        return obj.profiles_unlikes.count()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    User profile
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
        Adding first name and last name from built-in user model to Profile model
        """
        return f'{obj.user.first_name} {obj.user.last_name}'

    @admin.display(description='Photo')
    def profile_photo_tag(self, obj):
        """
        Profile's photo
        """
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="100" height="100"/>')
