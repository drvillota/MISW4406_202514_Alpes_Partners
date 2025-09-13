# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cambiar para usar el archivo con el nombre correcto
COPY afilidados-comisiones-requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY .env* /app/ 

EXPOSE 8080

CMD ["python", "-m", "src.app.main"]
