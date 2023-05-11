from decimal import Decimal
from typing import NoReturn, Generator, Union
from copy import deepcopy
from django.conf import settings

from coupons.models import Coupon
from goods.models import Product
from django.core.exceptions import ObjectDoesNotExist

from present_cards.models import PresentCard


class Cart:
    """
    Корзина с товарами
    """

    @property
    def coupon(self) -> Union[Coupon, None]:
        """
        Возвращает объект купона или None
        """
        try:
            coupon = Coupon.objects.get(id=self.coupon_id)
        except ObjectDoesNotExist:
            return None
        return coupon

    @property
    def present_card(self) -> Union[PresentCard, None]:
        """
        Возвращает объект подарочной карты или None
        """
        try:
            present_card = PresentCard.objects.get(id=self.present_card_id)
        except ObjectDoesNotExist:
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

    def add(self, product: Product, quantity: int = 1) -> NoReturn:
        """
        Метод добавления товаров в корзину
        """
        product_id = str(product.pk)
        if product_id not in self.cart:
            self.cart[product_id] = {'price': str(product.price),
                                     'quantity': quantity}
        elif self.cart[product_id]['quantity'] != quantity:
            self.cart[product_id]['quantity'] = quantity

        self.session.modified = True

    def __len__(self) -> int:
        """
        Возвращает общее кол-во товаров с учетом кол-ва каждого товара
        """
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self) -> Generator[dict, None, None]:
        """
        Перебор всех товаров из корзины
        """
        products_ids = [pk for pk in self.cart]
        products = Product.objects.filter(id__in=products_ids)
        cart = deepcopy(self.cart)

        for pk, prod in zip(products_ids, products):
            cart[pk]['product'] = prod
            cart[pk]['price'] = Decimal(cart[pk]['price'])
            cart[pk]['total_price'] = Decimal(cart[pk]['price'] * cart[pk]['quantity'])

        for item in cart:
            yield cart[item]

    def remove(self, product_id: int) -> NoReturn:
        """
        Удаление информации о товаре с корзины по его id
        """
        if str(product_id) in self.cart:
            del self.cart[str(product_id)]

            self.session.modified = True

    def clear(self) -> NoReturn:
        """
        Очистка корзины с удалением купона и подарочной карты
        """
        del self.session[settings.CART_SESSION_ID]
        if 'coupon_id' in self.session:
            del self.session['coupon_id']
        if 'present_card_id' in self.session:
            del self.session['present_card_id']
        self.session.modified = True

    def get_total_price(self) -> Decimal:
        """
        Получение общей стоимости всех товаров с учетом их кол-ва
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_amount_items_in(self) -> int:
        """
        Получение количества разных товаров
        """
        return len(self.cart)

    def get_total_price_with_discounts(self) -> Decimal:
        """
        Расчет общей суммы заказа с учетом скидки от купона
        и/или вычета фиксированной суммы от подарочной карты
        """
        price_without_discount = self.get_total_price()
        coupon, present_card = self.coupon, self.present_card

        if coupon and present_card:
            result_amount = price_without_discount - (
                    (price_without_discount * coupon.discount / 100) + present_card.amount)
        elif coupon:
            result_amount = price_without_discount - (price_without_discount * coupon.discount / 100)
        elif present_card:
            result_amount = price_without_discount - present_card.amount
        else:
            result_amount = price_without_discount

        return Decimal(result_amount).quantize(Decimal('0.01'))

    def get_total_discount(self) -> Decimal:
        """
        Сумма скидки с учётом купона и/или подарочной карты
        """
        return self.get_total_price() - self.get_total_price_with_discounts()
