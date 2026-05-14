# Етап 1: Збірка залежностей (віртуальне середовище)
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --no-compile -r requirements.txt

# Етап 2: Запуск (мінімальний runtime)
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN useradd --create-home --uid 1000 app

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN chown -R app:app /app

USER app

# Немає локального HTTP як у nginx — перевіряємо, що головний процес (PID 1) живий.
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD kill -0 1 || exit 1

CMD ["python", "main.py"]
