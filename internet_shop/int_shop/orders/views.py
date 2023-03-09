from django.shortcuts import reverse
from typing import NoReturn
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from cart.cart import Cart
from orders.forms import OrderCreateForm, DeliveryCreateForm
from orders.models import Order, OrderItem


class OrderCreateView(LoginRequiredMixin, FormView):
    """
    Представление для создания заказа на сайте
    """
    form_class = OrderCreateForm
    template_name = 'orders/order_create.html'
    form_class_delivery = DeliveryCreateForm
    success_url = reverse_lazy('orders:order_created')

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView, self).get_context_data(**kwargs)
        context['order_form'] = self.form_class
        context['delivery_form'] = self.form_class_delivery
        return context

    def post(self, request, *args, **kwargs):
        cart = Cart(request)  # создаем объект корзины
        # получаем формы
        order_form = self.get_form()
        delivery_form = self.get_form(form_class=DeliveryCreateForm)

        if order_form.is_valid():
            order = order_form.save(commit=False)
            # если в корзине есть валидный купон и/или подарочная карта, присваиваем к заказу
            if cart.coupon:
                order.coupon = cart.coupon
            if cart.present_card:
                order.present_card = cart.present_card
        else:
            return self.form_invalid(order_form)

        if delivery_form.is_valid():
            delivery = delivery_form.save()
            order.delivery = delivery  # привязка доставки к заказу
            order.save()
            self.request.session['order_id'] = order.pk  # добавление id заказа в сессию
            self.create_order_items_from_cart(order)  # создание элементов заказа в базе
            return self.form_valid(order_form)
        else:
            return self.form_invalid(delivery_form)

    def create_order_items_from_cart(self, order: Order) -> NoReturn:
        """
        Создание элементов заказа в базе из элементов корзины,
        привязанных к текущему заказу
        """
        cart = Cart(self.request)
        for item in cart:
            OrderItem.objects.create(order=order,
                                     product=item['product'],
                                     price=item['price'],
                                     quantity=item['quantity'])
        cart.clear()


class OrderConfirmedView(TemplateView):
    template_name = 'orders/order_created.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_id'] = self.request.session.get('order_id')
        return context
