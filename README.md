📋 Концепция проекта
Система управления базой знаний для ответов на вопросы клиентов. Администратор может редактировать, 
удалять и дополнять базу знаний через Django Admin. Система анализирует входящие вопросы по ключевым словам и выдает релевантные ответы.

🧠
Анализ вопросов
Система использует TF-IDF + косинусное сходство для анализа вопросов клиентов и поиска ответов в базе знаний

🔍
Поиск по ключевым словам
Многоуровневый поиск: точное совпадение → ключевые слова → TF-IDF similarity

⚠️
Защита от дубликатов
При добавлении нового вопроса система проверяет наличие дубликата и уведомляет администратора

📝
Умное определение
Если вопрос сформулирован другими словами, но ответ есть — вопрос вносится в базу знаний

🔧
Django Admin
Полноценная админ-панель для управления базой знаний: CRUD операции, фильтрация, поиск

📊
Логи и статистика
Логирование всех поисковых запросов, подсчёт просмотров, отслеживание непопулярных вопросов

⚠️ Логика определения дубликатов

🚫
Дубликат найден
Если вопрос идентичен или очень похож (схожесть ≥ 75%) на существующий — система выдает уведомление: 
"Данные уже есть в базе знаний. Вопрос не будет добавлен."

✅
Другая формулировка
Если вопрос сформулирован другими словами (схожесть < 75%), но ответ уже существует — новый вопрос вносится в базу знаний как отдельная запись.

🆕
Новый вопрос
Если в базе знаний нет похожего вопроса — вопрос и ответ добавляются как новая запись.

🛠️ Технологический стек
Python 3.10+— Язык программирования
Django 4.2— Web-фреймворк
Django REST Framework— API
PostgreSQL— База данных
Gunicorn— WSGI сервер (порт 8092)
Nginx— Reverse proxy (порт 80)
systemd— Управление сервисами
scikit-learn— TF-IDF + Cosine Similarity
NLTK— Обработка текста
Ubuntu 22.04— Операционная система

📁 Структура проекта

/home/cubinez85/client_answer/
├── .env                          # Переменные окружения
├── manage.py                     # Django management
├── requirements.txt              # Зависимости Python
├── config/                       # Настройки проекта
│   ├── __init__.py
│   ├── settings.py               # Основные настройки
│   ├── urls.py                   # Корневые URL
│   └── wsgi.py                   # WSGI для Gunicorn
├── knowledge_base/               # App: База знаний
│   ├── __init__.py
│   ├── admin.py                  # Админ-панель
│   ├── models.py                 # Модели (QuestionAnswer, Category, SearchLog)
│   ├── services.py               # Сервис анализа схожести (TF-IDF)
│   ├── migrations/               # Миграции БД
│   └── tests.py
├── api/                          # App: REST API
│   ├── __init__.py
│   ├── urls.py                   # Маршруты API
│   ├── views.py                  # ViewSets
│   ├── serializers.py            # Сериализаторы DRF
│   └── tests.py
├── templates/                    # HTML шаблоны
├── static/                       # Статические файлы
├── staticfiles/                  # Собранные статики (collectstatic)
├── media/                        # Загруженные файлы
├── logs/                         # Логи Gunicorn
│   ├── access.log
│   └── error.log
└── venv/                         # Виртуальное окружение

🔄 Алгоритм обработки вопроса
1
Клиент отправляет вопрос через API (POST /api/search/)
2
Nginx проксирует запрос на Gunicorn (:8092)
3
Django принимает запрос, валидирует через Serializer
4
Поиск точного совпадения вопроса в БД
5
Если не найден — поиск по ключевым словам
6
Если не найден — TF-IDF + косинусное сходство
7
Если схожесть ≥ 75% — возвращаем найденный ответ
8
Логирование запроса в SearchLog
9
Возврат ответа клиенту

🗄️ Схема базы данных (PostgreSQL)
Category
🔑 id (PK)
• name (unique)
• description
• created_at
• updated_at

QuestionAnswer
🔑 id (PK)
• question (unique)
• answer
• keywords
🔗 category_id (FK)
• is_active
• view_count
• created_at
• updated_at

SearchLog
🔑 id (PK)
• query
• found
🔗 question_answer_id (FK)
• similarity_score
• ip_address
• created_at

⚡ Быстрый старт (все команды)
# === ПОЛНАЯ УСТАНОВКА ===

# 1. Обновление и установка пакетов
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx git

# 2. PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE client_answer_db;"
sudo -u postgres psql -c "CREATE USER cubinez85 WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE client_answer_db TO cubinez85;"

# 3. Проект
cd /home/cubinez85
git clone <your-repo> client_answer  # или создайте вручную
cd client_answer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Скачивание данных NLTK
python -c "import nltk; nltk.download('stopwords')"

# 4. Django
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput

# 5. Systemd
sudo cp client_answer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now client_answer

# 6. Nginx
sudo cp nginx_client_answer /etc/nginx/sites-available/client_answer
sudo ln -s /etc/nginx/sites-available/client_answer /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 7. Проверка
curl https://localhost/api/

⚠️ КРИТИЧЕСКИ ВАЖНЫЙ ШАГ: Права доступа
Поскольку Nginx на Ubuntu работает от пользователя www-data, а ваши папки staticfiles и media находятся в домашней директории
пользователя cubinez85, Nginx по умолчанию не сможет их прочитать и будет отдавать ошибку 403 Forbidden.
Выполните эти команды на хосте, чтобы открыть доступ:

# 1. Даем право на выполнение (вход) во все родительские папки до проекта
chmod o+x /home/cubinez85
chmod o+x /home/cubinez85/client_answer

# 2. Даем право на чтение статических и медиа файлов пользователю www-data
chmod -R o+r /home/cubinez85/client_answer/staticfiles
chmod -R o+r /home/cubinez85/client_answer/media

# 3. (Опционально, но рекомендуется) Делаем группу www-data владельцем этих папок, 
# чтобы Django (в Docker) и Nginx (на хосте) могли корректно работать с новыми файлами
sudo chown -R cubinez85:www-data /home/cubinez85/client_answer/staticfiles
sudo chown -R cubinez85:www-data /home/cubinez85/client_answer/media
chmod -R 775 /home/cubinez85/client_answer/staticfiles
chmod -R 775 /home/cubinez85/client_answer/media

🔌 API Endpoints
Django REST Framework API. Базовый URL: https://client-answer.cubinez.ru/api/

Метод	Путь            	                Описание	                                                   Авторизация
GET	/api/questions/	                        Список всех вопросов-ответов (с пагинацией)	                   Публичный
POST	/api/questions/	                        Создать новый вопрос-ответ (с проверкой на дубликат)	           Требуется авторизация
GET	/api/questions/{id}/	                Получить конкретный вопрос-ответ                                   Публичный
PUT	/api/questions/{id}/	                Обновить вопрос-ответ	                                           Требуется авторизация
DELETE	/api/questions/{id}/	                Удалить вопрос-ответ	                                           Требуется авторизация
POST	/api/questions/check_duplicate/	        Проверить вопрос на дубликат (без сохранения)	                   Требуется авторизация
POST	/api/search/	                        Найти ответ на вопрос клиента	                                   Публичный
GET	/api/search/popular/	                Популярные вопросы (по просмотрам)	                           Публичный
GET	/api/categories/	                Список категорий	                                           Публичный
POST	/api/categories/	                Создать категорию                                                  Требуется авторизация

📝 Примеры запросов
# Поиск ответа на вопрос

curl -X POST http://localhost/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Как вернуть товар?"}'

# Ответ:
{
    "found": true,
    "answer": "Для возврата товара необходимо обратиться в отдел...",
    "question": "Какова процедура возврата товара?",
    "category": "Возвраты",
    "similarity_score": 0.82,
    "method": "tfidf_similarity"
}

# Проверка на дубликат

curl -X POST http://localhost/api/questions/check_duplicate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your-token" \
  -d '{"question": "Как оформить возврат?"}'

# Ответ (дубликат найден):
{
    "is_duplicate": true,
    "existing_question": "Какова процедура возврата товара?",
    "similarity_score": 0.87,
    "message": "Внимание: найден похожий вопрос в базе знаний (схожесть: 87.0%). Вопрос не будет добавлен как дубликат."
}

# Ответ (дубликат НЕ найден):
{
    "is_duplicate": false,
    "existing_question": null,
    "similarity_score": 0.32,
    "message": "Дубликат не найден (макс. схожесть: 32.0%). Вопрос будет добавлен в базу знаний."
}

# Добавление вопроса-ответа

curl -X POST http://localhost/api/questions/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your-token" \
  -d '{
    "question": "Какие способы оплаты вы принимаете?",
    "answer": "Мы принимаем оплату банковскими картами Visa, MasterCard, МИР, а также через СБП.",
    "keywords": "оплата, карта, visa, mastercard, мир, сбп, оплата",
    "category": 1,
    "is_active": true
  }'

# Ответ (успешно):
{
    "message": "Вопрос-ответ успешно добавлен в базу знаний"
}

# Ответ (дубликат):
{
    "question": [
        "Дубликат найден! Похожий вопрос уже существует в базе знаний (схожесть: 81.0%): 'Какие способы оплаты доступны?'"
    ]
}


