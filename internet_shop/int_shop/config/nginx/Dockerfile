FROM nginx:stable-alpine
LABEL maintainer="volt.awp@gmail.com"

# создание папки с серитификатом ssl и его ключем
# создание pid файла
RUN mkdir -p /etc/ssl_cert/ && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    touch /var/run/nginx.pid

# копирование конфига и сертификатов
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./onlineshopproj.pp.ua.crt ./onlineshopproj.pp.ua.key /etc/ssl_cert/

# установка владельца для файла конфига, папки с кешем и pid файла
RUN chown -R nginx:www-data /etc/nginx/nginx.conf && \
    chown -R nginx:www-data /var/cache/nginx && \
    chown -R nginx:www-data /var/run/nginx.pid && \
    chown -R nginx:www-data /etc/ssl_cert && \
    chown -R nginx:www-data /vol && \
    chmod -R 755 /vol

# добавление пользователя в группу
RUN addgroup nginx www-data

ENV SERVER_NAME=onlineshopproj.pp.ua

USER nginx

CMD ["nginx", "-g", "daemon off;"]