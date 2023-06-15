from django.contrib import admin

from orders.models import Order, Delivery, OrderItem
from django.utils.safestring import mark_safe
from django.shortcuts import reverse


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
            'fields': ('comment', 'call_confirm', 'created', 'updated')
        })
    )

    @admin.display(description='Name')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    list_display = ['id', 'get_full_name', 'is_paid', 'is_done', 'get_discount']
    readonly_fields = ['created', 'updated']
    search_fields = ['last_name', 'phone']
    date_hierarchy = 'created'
    list_filter = ['is_paid']
    list_display_links = ['get_discount', 'get_full_name']

    @admin.display(description='Apply discount')
    def get_discount(self, obj):
        if obj.coupon:
            coupon_url = reverse(f'admin:coupons_coupon_change', args=(obj.coupon.pk,))
            return mark_safe(f'<a href="{coupon_url}">Coupon</a>')
        if obj.present_card:
            card_url = reverse(f'admin:present_cards_presentcard_change', args=(obj.present_card.pk,))
            return mark_safe(f'<a href="{card_url}">Present Card</a>')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'method', 'service', 'office_number', 'delivery_date']
    search_fields = ['last_name']
    date_hierarchy = 'delivery_date'
    list_filter = ['service', 'method']

    @admin.display(description='Name')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['pk', 'order', 'product', 'price', 'quantity']
    list_filter = ['order', 'product']
