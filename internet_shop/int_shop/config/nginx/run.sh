#!/bin/sh

set -e

# проверка dhparams и создание их, если еще нет

echo "Checking for dhparams.pem"
if [ ! -f "vol/proxy/ssl-dhparams.pem" ]; then
  echo "dhparams.pem doesn't exist - creating it..."
  openssl dhparams -out /vol/proxy/ssl-dhparams.pem 2048
fi

# Избежание замены параметров с envsubst
export host=\$host
export request_uri=\$request_uri

echo "Checking for fullchain.pem"
if [ ! -f "/etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem" ]; then
  echo "No SSL cert, enabling HTTP only.."
else
  echo "SSL cert exists, enabling HTTPS..."
fi

nginx -g 'deamon off;'
