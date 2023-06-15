from typing import NoReturn
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from account.models import Profile
from cart.cart import Cart
from .forms import OrderCreateForm, DeliveryCreateForm
from orders.models import Order, OrderItem
from orders.tasks import order_created
from django.http.response import HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site


class OrderCreateView(LoginRequiredMixin, FormView):
    """
    Представление для создания заказа на сайте
    """
    form_class = OrderCreateForm
    template_name = 'orders/order_create.html'
    success_url = reverse_lazy('orders:order_created')

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView, self).get_context_data(**kwargs)
        context['delivery_form'] = DeliveryCreateForm()
        context['form'].fields['email'].initial = self.request.user.email
        context['form'].fields['first_name'].initial = self.request.user.first_name
        context['form'].fields['last_name'].initial = self.request.user.last_name
        return context

    def post(self, request, *args, **kwargs):
        cart = Cart(request)  # создаем объект корзины
        profile = Profile.objects.get(user=self.request.user)
        # получаем формы
        order_form = self.get_form()
        delivery_form = self.get_form(form_class=DeliveryCreateForm)

        order_valid = order_form.is_valid()
        delivery_valid = delivery_form.is_valid()

        if all([order_valid, delivery_valid]):
            order = order_form.save(commit=False)
            # если в корзине есть валидный купон и/или подарочная карта, присваиваем к заказу
            if cart.coupon:
                order.coupon = cart.coupon
            if cart.present_card:
                order.present_card = cart.present_card

            delivery = delivery_form.save()
            # привязка доставки и профиля к заказу
            order.delivery = delivery
            order.profile = profile
            order.save()
            self.create_order_items_from_cart(order)  # создание элементов заказа в базе
            self.request.session['order_id'] = order.pk

            domain = get_current_site(request).domain
            is_secure = request.is_secure()
            # отправка сообщения о завершении заказа на почту
            order_created.delay(data={'domain': domain, 'is_secure': is_secure},
                                order_id=order.pk,
                                profile_username=profile.user.username)
            return HttpResponseRedirect(self.success_url)
        else:  # возврат форм с ошибками
            return self.render_to_response(context={'form': order_form,
                                                    'delivery_form': delivery_form})

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
        order = Order.objects.get(pk=self.request.session.get('order_id'))
        context['order_id'] = order.pk
        context['method'] = order.pay_method
        return context
