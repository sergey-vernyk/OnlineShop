FROM certbot/certbot:v1.27.0
LABEL maintainer="volt.awp@gmail.com"

ARG user="nginx"

# copying the script and grant to it executable permission
COPY certify-init.sh /opt/
RUN chmod +x /opt/certify-init.sh

RUN addgroup www-data && \
    adduser -D $user www-data

RUN mkdir -p /home/$user/letsencrypt /home/$user/lib/letsencrypt /home/$user/log/letsencrypt && \
    chown -R $user:www-data /home/$user/letsencrypt /home/$user/lib/letsencrypt /home/$user/log/letsencrypt

# overriding etrypoint
ENTRYPOINT []

USER root

# command for renew certificate
CMD ["certbot", "renew"]
