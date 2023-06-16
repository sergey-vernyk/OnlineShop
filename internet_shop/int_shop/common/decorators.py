from django.http import HttpResponseBadRequest
from functools import wraps
from django.http.response import JsonResponse
from django.shortcuts import reverse, get_object_or_404
from django.urls import resolve
from urllib.parse import urlparse
from django.http.request import HttpRequest

from goods.models import Product


def ajax_required(func):
    """
    Декоратор проверяет, выполняется ли запрос через AJAX
    """

    @wraps(func)  # декоратор обновляет функцию-оболочку, копируя такие атрибуты как __name__ и __doc__
    def wrap(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponseBadRequest()  # возврат HttpResponseBadRequest, если запрос не AJAX
        return func(request, *args, **kwargs)  # иначе возврат переданной функции с ее аргументами

    return wrap


def auth_profile_required(func):
    """
    Декоратор проверяет аутентификацию пользователя,
    который совершает некое действие на страницах сайта,
    где требуется, что бы пользователь был аутентифицирован
    перед выполнением этого действия
    """

    @wraps(func)
    def wrap(*args, **kwargs):

        # проверка типа view (класс или функция) и получения объекта request c view
        # в view типа класс request всегда находится ана 2-й позиции
        request = args[0] if isinstance(args[0], HttpRequest) else args[1]

        if request.user.is_authenticated:
            return func(*args, **kwargs)

        referer = request.META.get('HTTP_REFERER')  # получение URL с которого был переход
        match = resolve(urlparse(referer)[2])  # получение всей информации из URL

        # получение адреса перехода после аутентификации
        if ('product_pk' and 'product_slug') in match.kwargs:
            obj = Product.objects.get(pk=match.kwargs['product_pk'], slug=match.kwargs['product_slug'])
            url_next = obj.get_absolute_url()
        else:
            url_next = reverse(match.view_name)

        reverse_url = f'{reverse("login")}?next={url_next}'
        return JsonResponse({'success': False, 'login_page_url': reverse_url}, status=401)

    return wrap
