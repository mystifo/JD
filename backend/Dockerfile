FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --upgrade pip && pip install -r requirements/prod.txt \
    && pip install -r requirements/dev.txt

COPY . .

RUN useradd --create-home --shell /bin/bash herspace \
    && mkdir -p /app/private_storage /app/staticfiles \
    && chown -R herspace:herspace /app
USER herspace

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2"]
