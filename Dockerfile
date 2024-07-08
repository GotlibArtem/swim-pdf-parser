# Используем официальный образ Python
FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /app

# переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Обновляем pip
RUN pip install --upgrade pip

# Копируем файл зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY .env /app/.env

# Команда для выполнения миграций и запуска встроенного сервера разработки Django
CMD ["sh", "-c", "python swim_graph/manage.py migrate && python swim_graph/manage.py runserver 0.0.0.0:8000"]
