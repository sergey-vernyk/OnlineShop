FROM python:3.9-alpine3.16

# переменные нужны для работы с python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 5000
WORKDIR /code
ARG user=shop_admin

# пакеты для подключения postgresql
RUN apk update && apk add postgresql-client build-base postgresql-dev linux-headers nano
# папка для сокета postgresql и сокета uwsgi сервера
RUN mkdir -p /var/run/postgresql /var/run/wsgi
RUN chown postgres:postgres /var/run/postgresql/

# создание и назначения пользователя от которого будут запускаться команды в контейнере
RUN adduser -D $user
RUN addgroup $user www-data
RUN chown $user:www-data /var/run/wsgi
USER $user

# установка зависимостей
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# добавление пути в PATH местонахождения приложений, установленных через pip
ENV PATH "$PATH:/home/$user/.local/bin"

COPY . /code