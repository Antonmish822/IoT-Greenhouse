FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY frontend/requirements.txt ./requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY frontend/ ./

EXPOSE 8010

CMD ["python", "manage.py", "runserver", "0.0.0.0:8010"]
