import json

from cart.cart import Cart
from common.moduls_init import redis
from goods.models import Product


def show_cart_content_coreapi(cart: Cart, user_id: int) -> Cart:
    """
    Returns `cart` with items and either coupon id or present card id,
    which are located in Redis.
    """
    coupon_id = redis.hget('present_card_id', f'user_id:{user_id}')
    present_card_id = redis.hget('coupon_id', f'user_id:{user_id}')
    items_in_cart = redis.hget('session_cart', f'user_id:{user_id}')

    # assign data to instance
    if items_in_cart:
        cart.cart = json.loads(items_in_cart)
    cart.coupon_id = coupon_id.decode('utf-8')
    cart.present_card_id = present_card_id.decode('utf-8')

    return cart


def remove_cart_content_coreapi(cart: Cart, user_id: int, product_id: int) -> None:
    """
    Remove item with `product_id` from `cart`. If there are no items in the cart,
    remove it from Redis too.
    """
    items_in_cart = redis.hget('session_cart', f'user_id:{user_id}')
    if items_in_cart:
        cart.cart = json.loads(items_in_cart)

    cart.remove(product_id)
    # clear cart data in Redis
    if not cart:
        if redis.hexists('coupon_id', f'user_id:{user_id}'):
            redis.hdel('coupon_id', f'user_id:{user_id}')
        elif redis.hexists('present_card_id', f'user_id:{user_id}'):
            redis.hdel('present_card_id', f'user_id:{user_id}')
        redis.hdel('session_cart', f'user_id:{user_id}')
    else:
        cart_as_bytes = json.dumps(cart.cart)
        redis.hset('session_cart', f'user_id:{user_id}', cart_as_bytes)


def add_cart_content_coreapi(cart: Cart, user_id: int, product: Product, quantity: int) -> None:
    """
    Add `product` to `cart` instance and save the cart in Redis.
    """
    items_in_cart = redis.hget('session_cart', f'user_id:{user_id}')
    if items_in_cart:
        cart.cart = json.loads(items_in_cart)
    
    # add data also to Redis
    cart.add(product, int(quantity))
    cart_as_bytes = json.dumps(cart.cart)
    redis.hset('session_cart', f'user_id:{user_id}', cart_as_bytes)
