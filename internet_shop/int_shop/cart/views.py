from django.shortcuts import render, get_object_or_404
from .cart import Cart
from common.decorators import ajax_required
from cart.forms import CartQuantityForm
from coupons.forms import CouponApplyForm
from coupons.models import Coupon
from goods.models import Product
from present_cards.forms import PresentCardApplyForm
from present_cards.models import PresentCard
from django.http.response import JsonResponse
from django.views.decorators.http import require_POST


@ajax_required
@require_POST
def cart_add(request):
    """
    Добавление товара в корзину
    """

    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')

    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartQuantityForm(request.POST)
    if form.is_valid():
        cart.add(product, quantity=int(quantity))

    return JsonResponse({'success': True,
                         'cart_len': len(cart),
                         'added_prod_cost': cart.cart[product_id]['quantity'] * (
                                 product.promotional_price or product.price
                         ),
                         'total_price': cart.get_total_price(),
                         'total_price_discounts': cart.get_total_price_with_discounts(),
                         'total_discount': cart.get_total_discount()})


def cart_detail(request):
    """
    Отображения корзины с товарами (если они там есть)
    """
    coupon_code = None
    present_card_code = None

    # если купон был применен, отобразить его код в форме
    if request.session.get('coupon_id'):
        coupon_code = Coupon.objects.get(id=request.session.get('coupon_id'))

    # если подарочная карта была применена, отобразить ее код в форме
    if request.session.get('present_card_id'):
        present_card_code = PresentCard.objects.get(id=request.session.get('present_card_id'))
    #  заполняем форму принятыми кодами купона, если они были применены
    coupon_form = CouponApplyForm(initial={'code': coupon_code.code if coupon_code else ''})
    present_card_form = PresentCardApplyForm(initial={'code': present_card_code.code if present_card_code else ''})
    return render(request, 'cart/detail.html', {'cart': Cart(request),
                                                'coupon_form': coupon_form,
                                                'present_card_form': present_card_form})


@ajax_required
@require_POST
def cart_remove(request):
    """
    Удаление товара с корзины
    """
    prev_url = None
    product_id = request.POST.get('product_id')
    cart = Cart(request)
    cart.remove(product_id)
    if not cart:  # если больше нет товаров в корзине - удалить примененные купон или карту
        cart.clear()
        prev_url = request.session.get('urls')['previous_url']
    return JsonResponse({'success': True,
                         'cart_len': len(cart),
                         'total_price': cart.get_total_price(),
                         'total_price_discount': cart.get_total_price_with_discounts(),
                         'total_discount': cart.get_total_discount(),
                         'prev_url': prev_url})
