from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from account.models import Profile
from cart.cart import Cart
from orders.models import Order, OrderItem
from orders.tasks import order_created
from .forms import OrderCreateForm, DeliveryCreateForm


class OrderCreateView(LoginRequiredMixin, FormView):
    """
    View for creation order
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
        cart = Cart(request)  # creating cart instance
        profile = Profile.objects.get(user=self.request.user)
        # getting forms
        order_form = self.get_form()
        delivery_form = self.get_form(form_class=DeliveryCreateForm)

        order_valid = order_form.is_valid()
        delivery_valid = delivery_form.is_valid()

        if all([order_valid, delivery_valid]):
            order = order_form.save(commit=False)
            # if there are valid coupon or valid present card in the cart, linking them to the order
            if cart.coupon:
                order.coupon = cart.coupon
            elif cart.present_card:
                order.present_card = cart.present_card

            delivery = delivery_form.save()
            # linking delivery and profile to the order
            order.delivery = delivery
            order.profile = profile
            order.save()
            self.create_order_items_from_cart(order)  # creating the order's items in DB
            self.request.session['order_id'] = order.pk

            domain = request.site.domain
            is_secure = request.is_secure()
            # send message about complete the order to user's email
            order_created.delay(data={'domain': domain,
                                      'is_secure': is_secure,
                                      'language': request.LANGUAGE_CODE},
                                order_id=order.pk,
                                profile_username=self.request.user.username)
            return HttpResponseRedirect(self.success_url)
        # returns forms with errors
        return self.render_to_response(context={'form': order_form,
                                                'delivery_form': delivery_form})

    def create_order_items_from_cart(self, order: Order) -> None:
        """
        Creating order's items in DB from cart items, linked with current order.
        """
        cart = Cart(self.request)
        for item in cart:
            OrderItem.objects.create(order=order,
                                     product=item['product'],
                                     price=item['price'],
                                     quantity=item['quantity'])
        cart.clear()


class OrderConfirmedView(TemplateView):
    """
    View for displaying page with info,that order has been created
    """
    template_name = 'orders/order_created.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = Order.objects.get(pk=self.request.session.get('order_id'))
        context['order_id'] = order.pk
        context['method'] = order.pay_method
        return context
