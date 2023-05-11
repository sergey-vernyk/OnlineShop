def prev_current_urls_middleware(get_response):
    """
    Middleware для сохранения текущего и предыдущего URL в сессии
    """
    urls = {'current_url': None, 'previous_url': None}

    def middleware(request):
        current_url = request.build_absolute_uri()  # получения текущего полного URI
        # сохранять текущий URL только если это не один и тот же URL
        # не URL debug_toolbar и не URL для AJAX запроса
        if urls['current_url'] != current_url and '__debug__' not in current_url and 'ajax' not in current_url:
            urls['previous_url'] = urls['current_url']  # перезапись прошлого "текущего" URL
            urls['current_url'] = current_url  # запись текущего URL
            request.session['urls'] = urls  # и сохранение URL'ов в сессию
        response = get_response(request)

        return response

    return middleware
