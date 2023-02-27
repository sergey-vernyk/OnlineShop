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
    list_display = ['profile_full_name', 'date_of_birth', 'created']
    inlines = [FavoriteInline, CommentInline]
    readonly_fields = ['user_photo_tag']

    def profile_full_name(self, obj):
        """
        Добавление имени и фамилии пользователя из встроенной модели
        в модель профиля
        """
        return f'{obj.user.first_name} {obj.user.last_name}'

    profile_full_name.short_description = 'Username'  # отображение названия поля в шапке админ сайта модели

    def user_photo_tag(self, obj):
        """
        Фото профиля пользователя
        """
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="100" height="100"/>')

    user_photo_tag.short_description = 'Photo'
