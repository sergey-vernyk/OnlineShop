from django.contrib import admin

from account.models import Profile
from goods.models import Favorite, Comment
from django.utils.html import mark_safe


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
    readonly_fields = ('user_name', 'user_email', 'product')
    fieldsets = (
        ('Comment', {
            'classes': ('collapse',),
            'fields': ('user_name', 'user_email', 'body', 'product'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Профиль пользователя
    """
    fields = ('profile_full_name', 'user', 'date_of_birth', 'gender', 'user_photo_tag', 'created', 'about')
    inlines = [FavoriteInline, CommentInline]
    readonly_fields = ['user', 'user_photo_tag', 'created', 'profile_full_name']

    @admin.display(description='Username')  # отображение названия поля в шапке админ сайта модели
    def profile_full_name(self, obj):
        """
        Добавление имени и фамилии пользователя из встроенной модели
        в модель профиля
        """
        return f'{obj.user.first_name} {obj.user.last_name}'

    @admin.display(description='Photo')
    def user_photo_tag(self, obj):
        """
        Фото профиля пользователя
        """
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="100" height="100"/>')
