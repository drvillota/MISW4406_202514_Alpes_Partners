# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/afilidados-comisiones-requirements.txt
RUN pip install --no-cache-dir -r /app/afilidados-comisiones-requirements.txt

COPY src /app/src
COPY .env* /app/ 

EXPOSE 8080

CMD ["python", "-m", "src.app.main"]
