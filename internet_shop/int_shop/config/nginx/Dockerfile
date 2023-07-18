FROM nginx:stable-alpine
LABEL maintainer="volt.awp@gmail.com"

# создание папки с серитификатом ssl и его ключем
# создание pid файла
RUN mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/proxy && \
    touch /var/run/nginx.pid

# копирование конфига и сертификатов
COPY ./nginx.conf.template /etc/nginx/nginx.conf.template
COPY ./nginx_ssl.conf.template /etc/nginx/nginx_ssl.conf.template
COPY ./uwsgi_params /etc/nginx/
COPY ./options-ssl-nginx.conf /etc/nginx/
COPY ./run.sh /run.sh

RUN apk add --no-cache openssl bash
RUN chmod +x /run.sh

# установка владельца для файла конфига, папки с кешем и pid файла
RUN chown -R nginx:www-data /etc/nginx/nginx.conf && \
    chown -R nginx:www-data /var/cache/nginx && \
    chown -R nginx:www-data /var/run/nginx.pid && \
    chown -R nginx:www-data /vol && \
    chmod -R 755 /vol


# добавление пользователя в группу
RUN addgroup nginx www-data
# том для работы с certbot
VOLUME /vol/www

CMD ["/run.sh"]