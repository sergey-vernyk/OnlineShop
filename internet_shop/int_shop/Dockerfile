FROM python:3.9-alpine3.16

# переменные нужны для работы с python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 5000
WORKDIR /code
# пакеты для подключения postgresql
RUN apk update && apk add postgresql-client build-base postgresql-dev nano

# установка зависимостей
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# создание и назначения пользователя от которого будут запускаться команды в контейнере
RUN adduser -D shop_admin
USER shop_admin

COPY . /code