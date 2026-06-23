"""Consultas ejecutivas de solo lectura para el Comité Directivo.

Este router no crea, modifica ni aprueba información. Lee únicamente templates
y reportes que ya fueron aprobados por la OAP.

Al integrarlo en SISPLAN-Búsqueda, ajusta solamente las dos importaciones de
dependencias (`get_db` y `require_roles`) a los nombres reales del proyecto.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_roles


router = APIRouter(
    prefix="/api/comite-directivo",
    tags=["Comité Directivo"],
    dependencies=[Depends(require_roles("ADMIN", "OAP", "DIRECTIVO", "CONSULTA"))],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/filtros", summary="Catálogos disponibles para el visor ejecutivo")
def obtener_filtros(db: DbSession, vigencia: int = Query(2026, ge=2020, le=2100)) -> dict:
    lineas = db.execute(
        text(
            """
            SELECT DISTINCT l.id, l.codigo, l.nombre
            FROM lineas_estrategicas l
            JOIN templates t ON t.linea_id = l.id
            WHERE t.vigencia = :vigencia
            ORDER BY l.codigo
            """
        ),
        {"vigencia": vigencia},
    ).mappings().all()
    dependencias = db.execute(
        text(
            """
            SELECT DISTINCT d.id, d.codigo, d.nombre
            FROM dependencias d
            JOIN templates t ON t.dependencia_id = d.id
            WHERE t.vigencia = :vigencia
            ORDER BY d.nombre
            """
        ),
        {"vigencia": vigencia},
    ).mappings().all()
    return {
        "vigencia": vigencia,
        "lineas": [dict(row) for row in lineas],
        "dependencias": [dict(row) for row in dependencias],
        "estados": ["Activo", "Modificado", "Nuevo", "Inactivo"],
        "meses": list(range(1, 13)),
    }


@router.get("/indicadores", summary="Indicadores aprobados para Comité Directivo")
def listar_indicadores(
    db: DbSession,
    vigencia: int = Query(2026, ge=2020, le=2100),
    mes: int = Query(1, ge=1, le=12),
    linea_id: int | None = Query(None),
    dependencia_id: int | None = Query(None),
    estado: str | None = Query(None),
    buscar: str | None = Query(None, max_length=150),
) -> dict:
    conditions = ["t.vigencia = :vigencia"]
    params: dict = {"vigencia": vigencia, "mes": mes}
    if linea_id is not None:
        conditions.append("t.linea_id = :linea_id")
        params["linea_id"] = linea_id
    if dependencia_id is not None:
        conditions.append("t.dependencia_id = :dependencia_id")
        params["dependencia_id"] = dependencia_id
    if estado:
        conditions.append("LOWER(t.estado_indicador) = LOWER(:estado)")
        params["estado"] = estado
    if buscar:
        conditions.append(
            "(LOWER(t.codigo) LIKE :buscar OR LOWER(t.nombre) LIKE :buscar "
            "OR LOWER(d.nombre) LIKE :buscar)"
        )
        params["buscar"] = f"%{buscar.strip().lower()}%"

    rows = db.execute(
        text(
            f"""
            WITH templates_vigentes AS (
                SELECT origen.*,
                       ROW_NUMBER() OVER (
                           PARTITION BY origen.codigo, origen.vigencia
                           ORDER BY origen.version DESC, origen.id DESC
                       ) AS orden_version
                FROM templates origen
                WHERE origen.vigencia = :vigencia
            ),
            ultima_revision AS (
                SELECT o.report_id, o.comentario, o.estado_aplicacion,
                       ROW_NUMBER() OVER (PARTITION BY o.report_id ORDER BY o.created_at DESC) AS orden
                FROM oap_revisiones o
            )
            SELECT
                t.id,
                t.codigo,
                t.nombre,
                t.objetivo,
                t.formula_display AS formula,
                t.unidad_medida AS unidad,
                t.meta_anual AS "metaAnual",
                t.periodicidad,
                t.estado_indicador AS estado,
                l.id AS "lineaId",
                l.codigo AS "lineaCodigo",
                l.nombre AS "lineaNombre",
                d.id AS "dependenciaId",
                d.codigo AS "dependenciaCodigo",
                d.nombre AS "dependenciaNombre",
                :mes AS mes,
                r.id AS "reporteId",
                r.resultado_numerico AS resultado,
                r.analisis_cualitativo AS analisis,
                r.logros_dificultades AS logros,
                r.observaciones_dependencia AS observaciones,
                ur.comentario AS "observacionOap",
                ur.estado_aplicacion AS "estadoObservacionOap"
            FROM templates_vigentes t
            JOIN lineas_estrategicas l ON l.id = t.linea_id
            JOIN dependencias d ON d.id = t.dependencia_id
            LEFT JOIN reporting_periods p
                   ON p.vigencia = t.vigencia AND p.mes = :mes
            LEFT JOIN formularios_respondidos r
                   ON r.template_id = t.id
                  AND r.period_id = p.id
                  AND r.estado = 'APROBADO'
            LEFT JOIN ultima_revision ur
                   ON ur.report_id = r.id AND ur.orden = 1
            WHERE t.orden_version = 1 AND {' AND '.join(conditions)}
            ORDER BY l.codigo, t.codigo
            """
        ),
        params,
    ).mappings().all()

    indicadores = [dict(row) for row in rows]
    con_reporte = sum(1 for item in indicadores if item["reporteId"] is not None)
    con_observacion = sum(1 for item in indicadores if item["observacionOap"])
    resultados = [float(item["resultado"]) for item in indicadores if item["resultado"] is not None]
    return {
        "meta": {
            "vigencia": vigencia,
            "mes": mes,
            "total": len(indicadores),
            "conReporte": con_reporte,
            "sinReporte": len(indicadores) - con_reporte,
            "observacionesOap": con_observacion,
            "promedio": round(sum(resultados) / len(resultados), 2) if resultados else None,
        },
        "items": indicadores,
    }


@router.get("/indicadores/{template_id}", summary="Detalle anual aprobado de un indicador")
def obtener_indicador(
    template_id: int,
    db: DbSession,
    vigencia: int = Query(2026, ge=2020, le=2100),
) -> dict:
    template = db.execute(
        text(
            """
            SELECT t.id, t.codigo, t.nombre, t.objetivo,
                   t.definicion_operativa AS definicion,
                   t.formula_display AS formula, t.unidad_medida AS unidad,
                   t.meta_anual AS "metaAnual", t.periodicidad,
                   t.estado_indicador AS estado,
                   l.codigo AS "lineaCodigo", l.nombre AS "lineaNombre",
                   d.codigo AS "dependenciaCodigo", d.nombre AS "dependenciaNombre"
            FROM templates t
            JOIN lineas_estrategicas l ON l.id = t.linea_id
            JOIN dependencias d ON d.id = t.dependencia_id
            WHERE t.id = :template_id AND t.vigencia = :vigencia
            """
        ),
        {"template_id": template_id, "vigencia": vigencia},
    ).mappings().first()
    if template is None:
        raise HTTPException(status_code=404, detail="Indicador no encontrado")

    reportes = db.execute(
        text(
            """
            SELECT r.id, p.mes, r.resultado_numerico AS resultado,
                   r.analisis_cualitativo AS analisis,
                   r.logros_dificultades AS logros,
                   r.observaciones_dependencia AS observaciones,
                   r.approved_at AS "fechaAprobacion"
            FROM formularios_respondidos r
            JOIN reporting_periods p ON p.id = r.period_id
            WHERE r.template_id = :template_id
              AND p.vigencia = :vigencia
              AND r.estado = 'APROBADO'
            ORDER BY p.mes
            """
        ),
        {"template_id": template_id, "vigencia": vigencia},
    ).mappings().all()

    resultados = []
    for reporte in reportes:
        valores = db.execute(
            text(
                """
                SELECT tv.posicion, tv.nombre, tv.descripcion,
                       fv.valor_periodo AS "valorPeriodo",
                       fv.valor_acumulado AS "valorAcumulado"
                FROM formulario_valores fv
                JOIN template_variables tv ON tv.id = fv.variable_id
                WHERE fv.report_id = :report_id
                ORDER BY tv.posicion
                """
            ),
            {"report_id": reporte["id"]},
        ).mappings().all()
        revision = db.execute(
            text(
                """
                SELECT o.comentario, o.estado_aplicacion AS estado, o.created_at AS fecha
                FROM oap_revisiones o
                WHERE o.report_id = :report_id
                ORDER BY o.created_at DESC
                LIMIT 1
                """
            ),
            {"report_id": reporte["id"]},
        ).mappings().first()
        item = dict(reporte)
        item["variables"] = [dict(row) for row in valores]
        item["observacionOap"] = dict(revision) if revision else None
        resultados.append(item)

    response = dict(template)
    response["vigencia"] = vigencia
    response["resultados"] = resultados
    return response
