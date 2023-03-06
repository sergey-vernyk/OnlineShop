from decimal import Decimal
from django.conf import settings

from coupons.models import Coupon
from goods.models import Product


class Cart:
    """
    Корзина с товарами
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get('coupon_id')

    def add(self, product: Product, quantity=1):
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

    def __len__(self):
        """
        Возвращает общее кол-во товаров с учетом кол-ва каждого товара
        """
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self):
        products_ids = [pk for pk in self.cart]
        products = Product.objects.filter(id__in=products_ids)
        cart = self.cart.copy()

        for pk, prod in zip(products_ids, products):
            cart[pk]['product'] = prod
            cart[pk]['price'] = Decimal(cart[pk]['price'])
            cart[pk]['total_price'] = Decimal(cart[pk]['price'] * cart[pk]['quantity'])

        for item in cart:
            yield cart[item]

    def remove(self, product_id):
        """
        Удаление информации о товаре с корзины по его id
        """
        if str(product_id) in self.cart:
            del self.cart[str(product_id)]

            self.session.modified = True

    def get_total_price(self):
        """
        Получение общей стоимости всех товаров с учетом их кол-ва
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def get_amount_items_in(self):
        """
        Получение количества разных товаров
        """
        return len(self.cart)

    def get_total_price_with_coupon(self):
        """
        Расчет общей суммы заказа с учетом скидок
        """
        if self.coupon_id:
            coupon = Coupon.objects.get(id=self.coupon_id)
            price_without_discount = self.get_total_price()
            discount = price_without_discount - (price_without_discount * coupon.discount / 100)
            return Decimal(discount).quantize(Decimal('0.01'))
        return self.get_total_price()

    def get_discount_coupon(self):
        """
        Сумма скидки с учётом купона
        """
        return self.get_total_price() - self.get_total_price_with_coupon()
