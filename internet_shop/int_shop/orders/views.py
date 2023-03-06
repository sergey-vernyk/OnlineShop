from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from orders.forms import OrderCreateForm, DeliveryCreateForm
from coupons.models import Coupon
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from present_cards.models import PresentCard


class OrderCreateView(LoginRequiredMixin, FormView):
    """
    Представление для создания заказа на сайте
    """
    form_class = OrderCreateForm
    template_name = 'orders/order_create.html'
    form_class_delivery = DeliveryCreateForm
    success_url = reverse_lazy('goods:product_list')  # TODO

    def get_context_data(self, **kwargs):
        context = super(OrderCreateView, self).get_context_data(**kwargs)
        context['order_form'] = self.form_class
        context['delivery_form'] = self.form_class_delivery
        return context

    def post(self, request, *args, **kwargs):
        # получаем формы
        order_form = self.get_form()
        delivery_form = self.get_form(form_class=DeliveryCreateForm)
        if order_form.is_valid():
            coupon_code = order_form.cleaned_data.get('coupon_code')
            present_card_code = order_form.cleaned_data.get('present_card_code')
            order = order_form.save(commit=False)
            # получаем объекты купона и подарочной карты
            coupon = self.get_obj(coupon_code, Coupon)
            present_card = self.get_obj(present_card_code, PresentCard)
            # если объекты валидные - привязываем к заказу
            if coupon:
                order.coupon = coupon
            if present_card:
                order.present_card = present_card
        else:
            return self.form_invalid(order_form)

        if delivery_form.is_valid():
            delivery = delivery_form.save()
            order.delivery = delivery  # привязка доставки к заказу
            order.save()
            return self.form_valid(order_form)
        else:
            return self.form_invalid(delivery_form)

    def get_obj(self, code, klass):
        """
        Возвращает объект купона или подарочной карты
        в зависимости от переданного класса klass или None
        """
        now = timezone.now()
        try:
            obj = klass.objects.get(code__iexact=code,
                                    valid_from__lte=now,
                                    valid_to__gt=now,
                                    active=True)
        except ObjectDoesNotExist:
            return None
        return obj
