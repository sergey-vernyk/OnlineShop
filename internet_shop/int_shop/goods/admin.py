from django.contrib import admin

from goods.models import Product, Category, Manufacturer, Comment, Property


class CommentInline(admin.StackedInline):
    """
    Комментарии для товара
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
    list_display = [field.name for field in Property._meta.get_fields()]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Товары
    """
    list_display = ['name', 'pk', 'manufacturer', 'price', 'created', 'updated', 'available', 'properties', 'rating']
    list_editable = ['price', 'available']
    list_filter = ['manufacturer', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    inlines = [CommentInline]
    save_on_top = True
    exclude = ('star',)


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
