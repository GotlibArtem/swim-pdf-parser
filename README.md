# Swim Graph

Веб-приложение для анализа результатов соревнований по плаванию.

## Описание

Это проект предназначен для автоматизации процесса анализа результатов соревнований по плаванию и включает в себя:
- парсинг PDF файлов, содержащих данные результатов соревнований;
- обработку и визуализацию результатов в виде таблиц и графиков.

В проекте используются Django для веб-фреймворка и Docker для контейнеризации приложения.

## Требования

- Docker
- Docker Compose

## Установка

### 1. Клонирование репозитория

Клонируйте репозиторий на ваш локальный ПК:

```sh
git clone https://github.com/bezrazli4n0/swim-graph.git
cd swim-graph
```

### 2. Создание файла .env с переменными окружения

Создайте файл .env в корневой директории проекта и добавьте туда необходимые переменные окружения:

```sh
POSTGRES_DB=your-postgres-db
POSTGRES_USER=your-postgres-user
POSTGRES_PASSWORD=your-postgres-password
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Запуск контейнеров Docker

Запустите контейнеры в фоновом режиме с помощью Docker Compose:

```sh
docker-compose up --build -d
```

### 4. Создание суперпользователя

Создайте суперпользователя для доступа к административной панели:

```sh
docker-compose run web python swim_graph/manage.py createsuperuser
```

### 5. Доступ к проекту

После успешного выполнения всех шагов проект будет доступен по адресу:

```sh
http://localhost:8000
```
