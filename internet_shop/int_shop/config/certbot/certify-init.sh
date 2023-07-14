#!/bin/sh

# Ожидание доступности прокси и затем получение сертификата

set -e

until nc -z nginx_static 80; do
  echo "Waiting for proxy..."
  sleep 5s &
  wait ${!}
done

echo "Getting certificate..."

certbot certonly \
  --webroot \
  --webroot-path "/vol/www/" \
  -d "$SERVER_NAME" \
  --email "$EMAIL" \
  --rsa-key-size 4096 \
  --agree-tos \
  --noninteractive
