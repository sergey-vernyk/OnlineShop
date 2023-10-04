from copy import deepcopy
from decimal import Decimal
from typing import Generator, Union

from django.conf import settings
from django.db.models import Case, When, Value

from coupons.models import Coupon
from goods.models import Product
from present_cards.models import PresentCard
from .forms import CartQuantityForm


class Cart:
    """
    Cart with products
    """

    @property
    def coupon(self) -> Union[Coupon, None]:
        """
        Returns coupon object or None
        """
        if self.coupon_id:
            coupon = Coupon.objects.get(id=self.coupon_id)
        else:
            return None
        return coupon

    @property
    def present_card(self) -> Union[PresentCard, None]:
        """
        Returns present card object or None
        """
        if self.present_card_id:
            present_card = PresentCard.objects.get(id=self.present_card_id)
        else:
            return None
        return present_card

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')
        self.present_card_id = self.session.get('present_card_id')

    def add(self, product: Product, quantity: int = 1):
        """
        Method adds product to the cart
        """
        product_id = str(product.pk)
        if product_id not in self.cart:
            self.cart[product_id] = {'price': str(product.promotional_price or product.price),
                                     'quantity': quantity}
        elif self.cart[product_id]['quantity'] != quantity:
            self.cart[product_id]['quantity'] = quantity

        self.session.modified = True

    def __len__(self) -> int:
        """
        Returns the total number of goods quantity, taking into account it quantity
        """
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self) -> Generator[dict, None, None]:
        """
        Getting of all products from the cart
        """
        products_ids = [pk for pk in self.cart]
        products_ids_ordered = Case(*[When(pk=pk, then=Value(position)) for position, pk in enumerate(products_ids)])
        # getting goods in order their id in products_ids
        products = Product.available_objects.filter(id__in=products_ids).order_by(products_ids_ordered)
        cart = deepcopy(self.cart)

        for pk, prod in zip(products_ids, products):
            cart[pk]['quantity_form'] = CartQuantityForm(initial={'quantity': cart[pk]['quantity']})
            cart[pk]['product'] = prod
            cart[pk]['price'] = Decimal(cart[pk]['price'])
            cart[pk]['total_price'] = Decimal(cart[pk]['price'] * cart[pk]['quantity'])

        for item in cart:
            yield cart[item]

    def remove(self, product_id: int):
        """
        Deleting info about product from the cart by product id
        """
        if str(product_id) in self.cart:
            del self.cart[str(product_id)]

            self.session.modified = True

    def clear(self):
        """
        Clearing the cart with deleting coupon and present card from session
        """
        del self.session[settings.CART_SESSION_ID]
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        if 'present_card_id' in self.session:
            del self.session['present_card_id']
        self.session.modified = True

    def get_total_price(self) -> int:
        """
        Getting total cost of all products taking into account it quantity
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_amount_items_in(self) -> int:
        """
        Getting quantity different products in the cart
        """
        return len(self.cart)

    def get_total_price_with_discounts(self) -> Decimal:
        """
        Calculating total order sum taking into account coupon discount
        or deduction of the fixed amount of present card
        """
        price_without_discount = self.get_total_price()
        coupon, present_card = self.coupon, self.present_card

        if coupon:
            result_amount = price_without_discount - (price_without_discount * coupon.discount / 100)
        elif present_card:
            result_amount = price_without_discount - present_card.amount
        else:
            result_amount = price_without_discount

        return Decimal(result_amount).quantize(Decimal('0.01'))

    def get_total_discount(self) -> Decimal:
        """
        Returns discount amount taking into account coupon or present card
        """
        return self.get_total_price() - self.get_total_price_with_discounts()
