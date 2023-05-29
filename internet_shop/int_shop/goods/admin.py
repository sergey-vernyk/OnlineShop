from django.contrib import admin

from goods.models import Product, Category, Manufacturer, Comment, Property, Favorite, PropertyCategory
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
    list_display = ['name', 'text_value', 'numeric_value', 'units', 'category_property', 'product']
    ordering = ['category_property', 'product', 'name']
    search_fields = ['product__name', 'category_property__name']
    list_per_page = 15
    list_filter = ['product', 'category_property']


@admin.register(PropertyCategory)
class PropertyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    filter_horizontal = ('product_categories',)
    list_filter = ['product_categories']


class PropertyInline(admin.StackedInline):
    model = Property
    extra = 0
    readonly_fields = ['category_property']
    fieldsets = (
        ('Property', {
            'classes': ('collapse',),
            'fields': (('name', 'text_value', 'numeric_value', 'units', 'category_property'),),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Товары
    """
    list_display = ['name', 'pk', 'manufacturer',
                    'price', 'created', 'updated',
                    'available', 'promotional', 'rating']
    readonly_fields = ['image_tag']
    list_editable = ['price', 'available']
    list_filter = ['manufacturer', 'category', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    inlines = [CommentInline, PropertyInline]
    save_on_top = True
    exclude = ('star',)

    @admin.display(description='Image')
    def image_tag(self, obj):
        """
        Отображение изображения товара
        """
        return mark_safe(f'<img src="{obj.image.url}" width="100" height="100"/>')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Категории товаров
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
