from django.conf import settings


def previous_and_current_urls_middleware(get_response):
    """
    Middleware for the save current and previous URLs into the session
    """
    urls = {'current_url': None, 'previous_url': None}
    # get only own applications (their name is part of the URL)
    all_apps = settings.INSTALLED_APPS
    own_apps = [app.split('.')[0] for app in all_apps if app.endswith('Config')]

    def middleware(request):
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.site.domain

        if urls['current_url'] is None:
            urls.update(current_url=f'{protocol}://{domain}')

        current_url = request.build_absolute_uri()  # getting current full URI
        split_url = current_url.split('/')
        if urls['current_url'] != current_url and ('ajax' not in current_url and split_url[3] in (
                own_apps or '' or split_url[3].startswith('?'))
        ):
            urls['previous_url'] = urls['current_url']
            urls['current_url'] = current_url
            request.session['urls'] = urls  # saving the URLs to the session
        response = get_response(request)

        return response

    return middleware
