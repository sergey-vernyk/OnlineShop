#!/bin/sh

# Waiting proxy availability  and then getting certificate

set -e

until nc -z nginx 80; do
  echo "Waiting for proxy..."
  sleep 5s &
  wait ${!}
done

echo "Getting certificate..."

certbot certonly \
  --webroot \
  --webroot-path "/vol/www/" \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --rsa-key-size 4096 \
  --agree-tos \
  --noninteractive \
  --config-dir "/home/nginx/letsencrypt/" \
  --work-dir "/home/nginx/lib/letsencrypt/" \
  --logs-dir "/home/nginx/log/letsencrypt/"
