from django.http import HttpResponseBadRequest
from functools import wraps


def ajax_required(f):
    """Декоратор проверяет, выполняется ли запрос через AJAX"""

    @wraps(f)  # декоратор обновляет функцию-оболочку, копируя такие атрибуты как __name__ и __doc__
    def wrap(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponseBadRequest()  # возврат HttpResponseBadRequest, если запрос не AJAX
        return f(request, *args, **kwargs)  # иначе возврат переданной функции с ее аргументами

    return wrap
