# backend/app/main.py
# Agregar únicamente estas dos líneas; no modificar el router de estadísticas.

from app.routers import comite_directivo

app.include_router(comite_directivo.router)
