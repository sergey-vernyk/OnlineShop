from django.contrib import admin

from orders.models import Order, Delivery, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Buyer info', {
            'fields': ('first_name', 'last_name', 'email', 'address', 'phone')
        }),
        ('Payment', {
            'fields': ('pay_method', 'is_paid', 'is_done', 'stripe_id')
        }),
        ('Discounts', {
            'fields': ('present_card', 'coupon')
        }),
        ('Delivery', {
            'fields': ('delivery',)
        }),
        ('Other', {
            'fields': ('comment', 'call_confirm', 'created', 'updated', 'is_email_was_sent')
        })
    )

    @admin.display(description='Name')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    list_display = ['id', 'get_full_name', 'is_paid', 'is_done', 'is_email_was_sent']
    readonly_fields = ['created', 'updated', 'is_email_was_sent']
    search_fields = ['last_name', 'phone']
    date_hierarchy = 'created'
    list_filter = ['is_email_was_sent', 'is_paid']


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'method', 'office_number', 'delivery_date']
    search_fields = ['last_name']
    date_hierarchy = 'delivery_date'

    @admin.display(description='Name')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['pk', 'order', 'product', 'price', 'quantity']
