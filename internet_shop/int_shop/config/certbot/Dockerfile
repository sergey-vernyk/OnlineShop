FROM certbot/certbot:v1.27.0
LABEL maintainer="volt.awp@gmail.com"

ARG user="nginx"

# копирование скрипта и назначение его как исполняемого
COPY certify-init.sh /opt/
RUN chmod +x /opt/certify-init.sh

RUN addgroup www-data && \
    adduser -D $user www-data

RUN mkdir -p /home/$user/letsencrypt /home/$user/lib/letsencrypt /home/$user/log/letsencrypt && \
    chown -R $user:www-data /home/$user/letsencrypt /home/$user/lib/letsencrypt /home/$user/log/letsencrypt

# переопределения entrypoint
ENTRYPOINT []

USER root

# команда для поновления сертификата
CMD ["certbot", "renew"]
