# Imagen de la aplicación: FastAPI + Jinja2 + SQLite (monolito modular).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LICEO_DB=/app/data/liceo.db

# 1) Dependencias primero: Docker reutiliza esta capa si requirements.txt no cambia.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Código de la aplicación y pruebas (para poder correr pytest dentro del contenedor).
COPY app ./app
COPY tests ./tests
COPY pytest.ini agregar_usuario.py ./

# 3) Usuario sin privilegios y carpeta de datos donde se montará el volumen de SQLite.
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
