FROM python:3.9-alpine3.16
LABEL maintainer="volt.awp@gmail.com"

# variales needeed for interaction with python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 5000
WORKDIR /code
ARG user=shop_admin

# packages for connection to postgresql
RUN apk update && \
    apk add --update --no-cache postgresql-client \
        build-base postgresql-dev linux-headers

# creating and assigning user from which will starts commands in the docker
RUN adduser -D $user && \
    addgroup $user www-data

# directories for sockets, logs files and result file with hash media files
# set owner for created directries and files
RUN mkdir -p /var/run/postgresql /var/run/wsgi /vol/web/static /vol/web/media /code/scripts /code/coverage && \
    touch /code/main_log.log /code/scripts/result_hash.txt && \
    chmod -R 755 /code/main_log.log /code/scripts/result_hash.txt /vol /code/coverage && \
    chown -R $user:$user /vol /code/main_log.log /code/scripts/result_hash.txt && \
    chown -R postgres:postgres /var/run/postgresql && \
    chown -R $user:www-data /var/run/wsgi

USER $user

# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# adding path to PATH environment variable, where located applications installed through pip
ENV PATH "$PATH:/home/$user/.local/bin"

# copy source code to docker
COPY . /code