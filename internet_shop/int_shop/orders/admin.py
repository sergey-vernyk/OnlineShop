from django.contrib import admin

from orders.models import Order, Delivery, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Buyer info', {
            'fields': ('first_name', 'last_name', 'email', 'address', 'phone')
        }),
        ('Payment', {
            'fields': ('pay_method', 'is_paid')
        }),
        ('Discounts', {
            'fields': ('present_card', 'coupon')
        }),
        ('Delivery', {
            'fields': ('delivery', 'recipient')
        }),
        ('Other', {
            'fields': ('comment', 'call_confirm', 'created', 'updated')
        })
    )

    readonly_fields = ['created', 'updated']
    search_fields = ['last_name', 'phone']
    date_hierarchy = 'created'


@admin.register(Delivery)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'method', 'office_number', 'delivery_date']
    search_fields = ['last_name']
    date_hierarchy = 'delivery_date'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'quantity']
