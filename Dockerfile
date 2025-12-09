# Використовуємо офіційний Python 3.12 (slim версія для економії місця)
FROM python:3.12-slim as builder

# Встановлюємо Poetry
RUN pip install poetry

# Налаштовуємо Poetry: не створювати віртуальне оточення (в Docker воно не треба)
ENV POETRY_VIRTUALENVS_CREATE=false

# Робоча директорія
WORKDIR /app

# Копіюємо файли залежностей
COPY pyproject.toml poetry.lock* ./

# Встановлюємо залежності (без dev-пакетів)
RUN poetry install --no-root --only main

# --- Фінальний етап ---
FROM python:3.12-slim

WORKDIR /app

# Копіюємо встановлені пакети з етапу builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копіюємо код проекту
COPY . .

# Змінні середовища для коректної роботи в контейнері
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# Відкриваємо порт
EXPOSE 8000

# Команда запуску сервера
CMD ["python", "-m", "app.server"]