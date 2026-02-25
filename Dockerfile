FROM python:3.11-slim

WORKDIR /opt/app

# Устанавливаем зависимости и утилиты
COPY requirements.txt .
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY . .

# Создаём директории для данных и логов
RUN mkdir -p logs data && chmod 755 logs data

# Инициализируем БД и запускаем Flask
CMD ["sh", "-c", "python database/init_db.py && python -m flask run --host=0.0.0.0 --port=5000"]
