# colaboraciones/colaboraciones.Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Si tus imports quedan como "from config.api import ..." o "from api.v1.router import ...",
# necesitamos que la carpeta src esté en el sys.path. Hacemos WORKDIR a /app/src
WORKDIR /app/src

# Instala dependencias
COPY colaboraciones-servicio-requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia sólo el código fuente (ya con imports relativos)
COPY src/ /app/src/

# Copia variables de entorno si las tienes
COPY .env* /app/

EXPOSE 8080

# Ejecuta uvicorn apuntando a main.py que está en /app/src/main.py
# Nota: usamos main:app porque ahora el WORKDIR es /app/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
