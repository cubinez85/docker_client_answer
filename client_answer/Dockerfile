# Используем легкий образ Python 3.10
FROM python:3.10-slim

# Переменные окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Установка системных зависимостей для psycopg2 и сборки
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем исходный код проекта
COPY . .

# Предварительная загрузка данных NLTK (чтобы не качать их при каждом запуске)
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

# Команда запуска (будет переопределена в docker-compose, но оставим как fallback)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8092", "--workers", "3"]
