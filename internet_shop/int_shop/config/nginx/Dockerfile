FROM nginx:stable-alpine
LABEL maintainer="volt.awp@gmail.com"

# directories for madia and static files
# creating pid file for nginx
RUN mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/proxy && \
    touch /var/run/nginx.pid

# copying configs
COPY ./nginx.conf.template \
     ./nginx_ssl.conf.template \
     ./options-ssl-nginx.conf \
     ./uwsgi_params /etc/nginx/

# copying script
COPY ./run.sh /run.sh

# adding software and grant execution permission to the script
RUN apk add --no-cache openssl bash
RUN chmod +x /run.sh

# setting owner for config file, cache directory and pid file
RUN chown -R nginx:www-data /etc/nginx/nginx.conf && \
    chown -R nginx:www-data /var/cache/nginx && \
    chown -R nginx:www-data /var/run/nginx.pid && \
    chown -R nginx:www-data /vol && \
    chmod -R 755 /vol

# adding user to the group
RUN addgroup nginx www-data
# volume for interaction with certbot
VOLUME /vol/www

CMD ["/run.sh"]
