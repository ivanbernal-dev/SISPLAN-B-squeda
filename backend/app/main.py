# ============================================================
# UBPD Backend — Punto de Entrada de FastAPI
# TODO: Implementar en pasos posteriores
# ============================================================

# Estructura de módulos planificada:
#
# app/
# ├── main.py                    ← Este archivo (entry point)
# ├── celery_app.py              ← Configuración de Celery
# ├── config.py                  ← Settings desde variables de entorno
# ├── database.py                ← Conexión async a PostgreSQL
# ├── dependencies.py            ← Dependencias FastAPI (auth guards)
# │
# ├── models/                    ← Modelos SQLAlchemy (tablas BD)
# │   ├── user.py
# │   ├── dependency.py
# │   ├── template.py
# │   ├── form.py
# │   ├── file.py
# │   ├── fact_stats.py
# │   ├── audit_log.py
# │   └── pipeline_run.py
# │
# ├── schemas/                   ← Schemas Pydantic (validación API)
# │   ├── auth.py
# │   ├── user.py
# │   ├── template.py
# │   ├── form.py
# │   ├── stats.py
# │   └── file.py
# │
# ├── routers/                   ← Endpoints de la API
# │   ├── auth.py
# │   ├── admin.py
# │   ├── templates.py
# │   ├── forms.py
# │   ├── files.py
# │   ├── validation.py
# │   └── stats.py
# │
# ├── services/                  ← Lógica de negocio
# │   ├── auth_service.py
# │   ├── template_parser.py     ← Markdown → JSONB
# │   ├── minio_service.py
# │   ├── pipeline_service.py
# │   └── calculators/           ← Lógica de indicadores
# │       ├── base_calculator.py
# │       └── indicator_1.py
# │
# └── tasks/                     ← Tareas Celery
#     ├── pipeline_tasks.py
#     └── scheduled_tasks.py

pass
