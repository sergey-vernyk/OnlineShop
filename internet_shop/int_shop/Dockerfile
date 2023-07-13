FROM python:3.9-alpine3.16
LABEL maintainer="volt.awp@gmail.com"

# переменные нужны для работы с python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 5000
WORKDIR /code
ARG user=shop_admin

# пакеты для подключения postgresql
RUN apk update && \
    apk add --update --no-cache postgresql-client \
        build-base postgresql-dev linux-headers nano

# создание и назначения пользователя от которого будут запускаться команды в контейнере
RUN adduser -D $user && \
    addgroup $user www-data

# папки для сокетов, файл лога, файл результат хеша файлов медиа
# установка владельца для созданных папок и файлов
RUN mkdir -p /var/run/postgresql /var/run/wsgi /vol/web/static /vol/web/media /code/scripts && \
    touch /code/main_log.log /code/scripts/result_hash.txt && \
    chmod -R 755 /code/main_log.log /code/scripts/result_hash.txt /vol && \
    chown -R $user:$user /vol /code/main_log.log /code/scripts/result_hash.txt && \
    chown -R postgres:postgres /var/run/postgresql && \
    chown -R $user:www-data /var/run/wsgi

USER $user

# установка зависимостей
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# добавление пути в PATH местонахождения приложений, установленных через pip
ENV PATH "$PATH:/home/$user/.local/bin"

COPY . /code