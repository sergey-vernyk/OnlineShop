from django.conf import settings


def prev_current_urls_middleware(get_response):
    """
    Middleware для сохранения текущего и предыдущего URL в сессии
    """
    urls = {'current_url': None, 'previous_url': None}

    def middleware(request):  # TODO
        current_url = request.build_absolute_uri()  # получения текущего полного URI
        # делим текущий URL, получаем все установленные приложения
        # получаем только свои приложения (которые являются частью URL)
        # сохранять текущий URL только если это не один и тот же URL
        # не URL для AJAX запроса и в URL есть строка с названием приложения
        split_url = current_url.split('/')
        all_apps = settings.__dict__['INSTALLED_APPS']
        own_apps = [app.split('.')[0] for app in all_apps if app.endswith('Config')]
        if urls['current_url'] != (current_url
                                   and 'ajax' not in current_url
                                   and split_url[3] in own_apps):
            urls['previous_url'] = urls['current_url']  # перезапись прошлого "текущего" URL
            urls['current_url'] = current_url  # запись текущего URL
            request.session['urls'] = urls  # и сохранение URL'ов в сессию
        response = get_response(request)

        return response

    return middleware
