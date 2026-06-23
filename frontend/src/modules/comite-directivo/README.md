# Comité Directivo

Visor ejecutivo de solo lectura. La pantalla consume
`GET /api/comite-directivo/indicadores` y no contiene indicadores incrustados.

Flujo de información:

1. El catálogo anual aporta la ficha estable de cada indicador.
2. El backend consulta únicamente formularios con estado `approved`.
3. Los reportes aprobados reemplazan el periodo correspondiente del catálogo.
4. El frontend presenta filtros, resultados, variables y comentarios OAP.

Este módulo no modifica `stats.py`, `BiDashboardView.vue` ni las rutas de
creación y validación de formularios.
