import base64
from random import choices, shuffle
from string import ascii_uppercase, digits
from typing import Union

from captcha.image import ImageCaptcha
from django.contrib import admin
from django.http.response import JsonResponse
from common.moduls_init import redis

NUMBER_OF_CAPTCHA_SYMBOLS = 6


class ValidDiscountsListFilter(admin.SimpleListFilter):
    """
    Filter by validity discounts in admin site (list_filter)
    """
    title = 'Validation status'  # human-readable title which will be displayed in the right admin sidebar
    parameter_name = 'validation_status'  # parameter for the filter that will be used in the URL query.

    def lookups(self, request, model_admin) -> [tuple, tuple]:
        """
        The first element in each tuple is the coded value for the option that will
        appear in the URL query. The second element is the human-readable name for
        the option that will appear in the right sidebar.
        """
        return [
            ('valid', 'Valid'),
            ('invalid', 'Invalid'),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via "self.value()"
        """
        if self.value() == 'valid':
            valid_ids = (x.id for x in queryset if x.is_valid)
            return queryset.filter(id__in=valid_ids)
        if self.value() == 'invalid':
            invalid_ids = (x.id for x in queryset if not x.is_valid)
            return queryset.filter(id__in=invalid_ids)


def create_captcha_image(request,
                         width: int = 200,
                         height: int = 60,
                         font_size: tuple = 35) -> Union[base64, JsonResponse]:
    """
    Method returns image for captcha in base64 format or Json response with this image
    """
    user_email = ''
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # if image creating occurs when user updating captcha by click on captcha (used AJAX)
    if request.method == 'POST' and is_ajax:
        width = int(request.POST.get('width'))
        height = int(request.POST.get('height'))
        font_size = int(request.POST.get('font_size'))
        user_email = request.POST.get('user_email')

    image = ImageCaptcha(width=width,
                         height=height,
                         fonts=['../int_shop/static/JetBrainsMono-Thin.ttf'],
                         font_sizes=(font_size,))
    random_captcha_text = create_random_text_for_captcha(NUMBER_OF_CAPTCHA_SYMBOLS)
    data = image.generate(random_captcha_text)  # generate image of the given text
    data.seek(0)  # make sure you're at the beginning of the BytesIO object
    captcha_image = data.read()
    base64_captcha_image = base64.b64encode(captcha_image).decode('utf-8')

    if user_email:
        redis.hset(f'user_register_captcha:{user_email}', 'captcha_text', random_captcha_text)

    result = JsonResponse({'success': True,
                           'captcha_image': base64_captcha_image}) \
        if request.method == 'POST' and is_ajax else base64_captcha_image

    return result


def create_random_text_for_captcha(symbols_num: int) -> str:
    """
    Methods returns random text for captcha, which was generated from ASCII uppercase letters and digits
    """
    digits_list = [digit for digit in digits]
    letters_list = [letter for letter in ascii_uppercase]
    symbols_set = digits_list + letters_list
    shuffle(symbols_set)
    # convert to string from list, cause choice returns list
    random_captcha_text = ''.join(choices(symbols_set, k=symbols_num))
    return random_captcha_text
