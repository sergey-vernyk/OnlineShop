from django.contrib import admin

from goods.models import Product, Category, Manufacturer, Comment, Property, Favorite
from django.utils.html import mark_safe


class CommentInline(admin.StackedInline):
    """
    Комментарии для товара под каждым товаром
    """
    model = Comment
    extra = 2
    readonly_fields = ['user_name', 'user_email', 'created', 'updated']
    fieldsets = (
        ('Comment', {
            'classes': ('collapse',),  # сворачивание комментария
            'fields': ('user_name', 'user_email', 'body', 'created', 'updated'),
        }),
    )


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Свойства товаров
    """
    list_display = [field.name for field in Property._meta.get_fields()]
    fieldsets = (
        ('Screen', {
            'fields': ('screen_diagonal', 'screen_resolution', 'screen_type',)
        }),
        ('CPU', {
            'fields': ('cpu', 'cpu_freq', 'cpu_cores',)
        }),
        ('RAM', {
            'fields': ('ram_type', 'ram_value',)
        }),
        ('ROM', {
            'fields': ('rom_type', 'rom_value',)
        }),
        ('Graphic', {
            'fields': ('graphics_type', 'graphics_ram_value',)
        }),
        ('Interfaces', {
            'fields': ('hdmi', 'wifi_type', 'usb_type', 'bluetooth',)
        }),
        ('Body', {
            'fields': ('dimensions', 'weight', 'material',)
        }),
        ('Camera', {
            'fields': ('camera_main', 'camera_front',)
        }),
        ('Battery', {
            'fields': ('battery_cap', 'quick_charge', 'charge_power',)
        }),
        ('Other', {
            'fields': ('operation_system', 'connection', 'work_time', 'equipment', 'sensors',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Товары
    """
    list_display = ['name', 'pk', 'manufacturer', 'price', 'created', 'updated', 'available', 'properties', 'rating']
    readonly_fields = ['image_tag']
    list_editable = ['price', 'available']
    list_filter = ['manufacturer', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    inlines = [CommentInline]
    save_on_top = True
    exclude = ('star',)

    def image_tag(self, obj):
        """
        Отображение изображения товара
        """
        return mark_safe(f'<img src="{obj.image.url}" width="100" height="100"/>')

    image_tag.short_description = 'Image'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Категории
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    """
    Производители
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['profile', 'created']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'user_email', 'body', 'created', 'updated']
    readonly_fields = ['user_name', 'user_email', 'product', 'profile']


admin.site.site_header = 'InterShop Admin'
admin.site.site_title = 'InterShop Admin'
admin.site.index_title = 'Administration content shop'
