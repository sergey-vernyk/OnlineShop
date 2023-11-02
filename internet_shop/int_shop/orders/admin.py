from django.contrib import admin
from django.shortcuts import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from orders.models import Order, Delivery, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin panel for orders.
    """
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

    @admin.display(description=_('Name'))
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    list_display = ['id', 'get_full_name', 'is_paid', 'is_done', 'get_discount', 'get_total_order_cost']
    readonly_fields = ['created', 'updated']
    search_fields = ['last_name', 'phone']
    date_hierarchy = 'created'
    list_filter = ['is_paid']
    list_display_links = ['get_discount', 'get_full_name']

    @admin.display(description=_('Apply discount'))
    def get_discount(self, obj):
        if obj.coupon:
            coupon_url = reverse('admin:coupons_coupon_change', args=(obj.coupon.pk,))
            return mark_safe(f'<a href="{coupon_url}">Coupon</a>')
        if obj.present_card:
            card_url = reverse('admin:present_cards_presentcard_change', args=(obj.present_card.pk,))
            return mark_safe(f'<a href="{card_url}">Present Card</a>')

    @admin.display(description=_('Total cost (discount)'))
    def get_total_order_cost(self, obj):
        values = obj.get_total_values()
        if values['total_cost_with_discounts']:
            return f'${values["total_cost"] - values["total_discounts"]} ( -${values["total_discounts"]} )'
        else:
            return f'${values["total_cost"]}'


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """
    Admin panel for delivery
    """
    list_display = ['pk', 'get_full_name', 'method', 'service', 'office_number', 'delivery_date']
    search_fields = ['last_name']
    date_hierarchy = 'delivery_date'
    list_filter = ['service', 'method', 'office_number']

    @admin.display(description='Name')
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin panel for order items
    """
    list_display = ['pk', 'order', 'product', 'price', 'quantity']
    list_filter = ['order', 'product']
