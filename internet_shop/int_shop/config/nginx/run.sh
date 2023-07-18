#!/bin/sh

set -e

# проверка dhparams и создание их, если еще нет

echo "Checking for dhparams.pem"
if [ ! -f "vol/proxy/ssl-dhparams.pem" ]; then
  echo "dhparams.pem doesn't exist - creating it..."
  openssl dhparam -out /vol/proxy/ssl-dhparams.pem 2048
else
  echo "dhparams.pem have found"
fi

# Избежание замены параметров с envsubst
export host=\$host
export request_uri=\$request_uri

echo "Checking for fullchain.pem"

if [ ! -f "/home/nginx/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "No SSL cert, enabling HTTP only.."
  envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf
else
  echo "SSL cert exists, enabling HTTPS..."
  envsubst < /etc/nginx/nginx_ssl.conf.template > /etc/nginx/conf.d/default.conf
fi


nginx -g 'daemon off;'
