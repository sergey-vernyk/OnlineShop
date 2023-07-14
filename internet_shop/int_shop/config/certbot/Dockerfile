FROM certbot/certbot:1.27.0

# копирование скрипта и назначение его как исполняемого
COPY certify-init.sh /opt/
RUN chmod +x /opt/certify-init.sh

# переопределения entrypoint
ENTRYPOINT []

# комманда для поновления сертификата
CMD ["certbot", "renew"]