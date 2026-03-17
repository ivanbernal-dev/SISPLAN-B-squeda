# ============================================================
# UBPD Backend — FastAPI
# ============================================================

FROM python:3.12-slim

# Variables de build
ARG APP_ENV=production

# Metadatos
LABEL maintainer="UBPD Dev Team"
LABEL description="Backend FastAPI para UBPD - Sistema de Formularios"

# Prevenir que Python escriba .pyc y deshabilitar buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=${APP_ENV}

WORKDIR /app

# Instalar dependencias del sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
# (se hace antes que el código para aprovechar caché de Docker)
COPY requirements.txt .

# Si hay wheels locales (modo air-gapped), instalar desde ahí
# Si no, instalar desde PyPI (requiere internet en build time)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear usuario no-root para seguridad
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Puerto interno del backend
EXPOSE 8000

# Comando de inicio:
# - En producción: múltiples workers Uvicorn
# - En desarrollo: 1 worker con hot-reload (montar ./backend:/app en compose)
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers"]
