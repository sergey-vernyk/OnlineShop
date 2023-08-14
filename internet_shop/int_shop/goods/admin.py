from django.contrib import admin

from goods.models import Product, Category, Manufacturer, Comment, Property, Favorite, PropertyCategory
from django.utils.html import mark_safe
from django_summernote.admin import SummernoteModelAdmin


class CommentInline(admin.StackedInline):
    """
    Comments under each product in detail product info
    """
    model = Comment
    extra = 2
    readonly_fields = ['user_name', 'user_email', 'created', 'updated']
    fieldsets = (
        ('Comment', {
            'classes': ('collapse',),  # collapse comment
            'fields': ('user_name', 'user_email', 'body', 'created', 'updated'),
        }),
    )


@admin.register(Property)
class PropertyAdmin(SummernoteModelAdmin):
    """
    Product property
    """
    list_display = ['name', 'text_value', 'numeric_value', 'units', 'category_property', 'product']
    ordering = ['category_property', 'product', 'name']
    search_fields = ['product__name', 'category_property__name']
    list_per_page = 15
    list_filter = ['product', 'category_property', 'name']
    summernote_fields = ('detail_description',)


@admin.register(PropertyCategory)
class PropertyCategoryAdmin(admin.ModelAdmin):
    """
    Product category
    """
    list_display = ['name']
    filter_horizontal = ('product_categories',)
    list_filter = ['product_categories']


class PropertyInline(admin.StackedInline):
    """
    Product properties under each product in detail product info
    """
    model = Property
    extra = 0
    fieldsets = (
        ('Property', {
            'classes': ('collapse',),
            'fields': (('name', 'text_value',
                        'numeric_value', 'units',
                        'category_property', 'detail_description'),),
        }),
    )


@admin.register(Product)
class ProductSummernoteAdmin(SummernoteModelAdmin):
    """
    Full product information
    """
    list_display = ['name', 'pk', 'manufacturer',
                    'price', 'promotional_price', 'created', 'updated',
                    'available', 'promotional', 'rating']
    readonly_fields = ['image_tag']
    list_editable = ['price', 'available']
    list_filter = ['manufacturer', 'category', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    inlines = [CommentInline, PropertyInline]
    save_on_top = True
    exclude = ('star',)
    summernote_fields = ('description',)

    @admin.display(description='Image')
    def image_tag(self, obj):
        """
        Displaying product image
        """
        return mark_safe(f'<img src="{obj.image.url}" width="100" height="100"/>')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Product categories
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    """
    Manufactures
    """
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Profile's favorites products
    """
    list_display = ['profile', 'created']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    All comments of products
    """
    list_display = ['user_name', 'user_email', 'body', 'created', 'updated']
    readonly_fields = ['user_name', 'user_email', 'product', 'profile']
    list_filter = ['created', 'user_email']


admin.site.site_header = 'OnlineShop Admin'
admin.site.site_title = 'OnlineShop Admin'
admin.site.index_title = 'Administration Shop content'
