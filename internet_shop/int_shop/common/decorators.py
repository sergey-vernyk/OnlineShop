from functools import wraps
from urllib.parse import urlparse

from django.http import HttpResponseBadRequest
from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.shortcuts import reverse
from django.urls import resolve

from goods.models import Product


def ajax_required(func):
    """
    Decorator checks, whether performing AJAX request
    """

    @wraps(func)  # decorator updates function-wrapper, copying attributes such as __name__ and __doc__
    def wrap(request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponseBadRequest()  # return HttpResponseBadRequest, if request is not AJAX
        return func(request, *args, **kwargs)  # else return passed function with their arguments

    return wrap


def auth_profile_required(func):
    """
    Decorator checks user's authentication, when user performs some action
    on the site's pages, where requires being user is authenticated before
    performs that action
    """

    @wraps(func)
    def wrap(*args, **kwargs):
        # checking view type (class or function) and getting request object along with view
        # if type of view is the class - request is always located on position 2
        request = args[0] if isinstance(args[0], HttpRequest) else args[1]

        if request.user.is_authenticated:
            return func(*args, **kwargs)

        referer = request.META.get('HTTP_REFERER')  # getting the URL from which the transition was made
        match = resolve(urlparse(referer)[2])  # getting all information from the URL

        # getting transition address after authentication
        if ('product_pk' and 'product_slug') in match.kwargs:
            obj = Product.objects.get(pk=match.kwargs['product_pk'], slug=match.kwargs['product_slug'])
            url_next = obj.get_absolute_url()
        else:
            url_next = reverse(match.view_name, kwargs=match.kwargs)

        reverse_url = f'{reverse("login")}?next={url_next}'
        return JsonResponse({'success': False, 'login_page_url': reverse_url}, status=401)

    return wrap
