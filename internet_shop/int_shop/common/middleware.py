from django.conf import settings


def previous_and_current_urls_middleware(get_response):
    """
    Middleware для сохранения текущего и предыдущего URL в сессии
    """
    urls = {'current_url': None, 'previous_url': None}
    # получаем только свои приложения (имя которых является частью URL)
    all_apps = settings.INSTALLED_APPS
    own_apps = [app.split('.')[0] for app in all_apps if app.endswith('Config')]

    def middleware(request):
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.site.domain

        if urls['current_url'] is None:
            urls.update(current_url=f'{protocol}://{domain}')
            
        current_url = request.build_absolute_uri()  # получения текущего полного URI
        split_url = current_url.split('/')
        if urls['current_url'] != current_url and ('ajax' not in current_url and split_url[3] in (
                own_apps or '' or split_url[3].startswith('?'))
        ):
            urls['previous_url'] = urls['current_url']
            urls['current_url'] = current_url
            request.session['urls'] = urls  # сохранение URL'ов в сессию
        response = get_response(request)

        return response

    return middleware
