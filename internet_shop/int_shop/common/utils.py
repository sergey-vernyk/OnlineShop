import base64
from random import choices, shuffle
from string import ascii_uppercase, digits
from typing import Union

import phonenumbers
from captcha.image import ImageCaptcha
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.http.response import JsonResponse
from django.utils.translation import gettext_lazy as _
from phonenumbers import carrier

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
            ('valid', _('Valid')),
            ('invalid', _('Invalid')),
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
        return queryset


def check_phone_number(phone_number: str) -> Union[str, bool]:
    """
    Return phone number if it is correct, otherwise return False
    """
    phone_number_output = ''.join(num.strip('()') for num in phone_number.split())
    phone_number_parse = phonenumbers.parse(phone_number_output, 'UA')
    carrier_of_number = carrier.name_for_number(phone_number_parse, 'en')
    if phonenumbers.is_possible_number(phone_number_parse) and carrier_of_number in (
            'Kyivstar',
            'Vodafone',
            'lifecell'
    ):
        return phone_number_output
    return False


def create_captcha_image(request,
                         width: int = 200,
                         height: int = 60,
                         font_size: int = 35) -> Union[str, JsonResponse]:
    """
    Method returns image for captcha in base64 format or Json response with this image
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # if image creating occurs when user updating captcha by click on captcha (used AJAX)
    if request.method == 'POST' and is_ajax:
        width = int(request.POST.get('width'))
        height = int(request.POST.get('height'))
        font_size = int(request.POST.get('font_size'))

    image = ImageCaptcha(width=width,
                         height=height,
                         fonts=['../int_shop/static/JetBrainsMono-Thin.ttf'],
                         font_sizes=(font_size,))
    random_captcha_text = create_random_text_for_captcha(NUMBER_OF_CAPTCHA_SYMBOLS)
    data = image.generate(random_captcha_text)  # generate image of the given text
    data.seek(0)  # make sure we're at the beginning of the BytesIO object
    captcha_image = data.read()
    base64_captcha_image = base64.b64encode(captcha_image).decode('utf-8')

    # save captcha text to redis and set expire their key on 10 minutes
    redis.hset(f'captcha:{random_captcha_text}', 'captcha_text', random_captcha_text)
    redis.expire(f'captcha:{random_captcha_text}', time=600, nx=True)

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


def validate_captcha_text(cleaned_data: dict) -> str:
    """
    Validating captcha text, which user is entering on pages with captcha.
    """

    captcha = cleaned_data.get('captcha').upper()  # convert all symbols to upper case as well

    redis_captcha = redis.hget(f'captcha:{captcha}', 'captcha_text')
    if redis_captcha:
        decode_captcha = redis_captcha.decode('utf-8').upper()
    else:
        raise ValidationError(_('Captcha is not correct'), code='wrong_captcha')

    return decode_captcha
