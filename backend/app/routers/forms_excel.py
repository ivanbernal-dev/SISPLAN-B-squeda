"""
app/routers/forms_excel.py — Endpoints para carga y descarga de formularios via Excel.

La clave interna de cada campo en configuracion_campos es "type" (no "tipo").
La carga valida campos requeridos, tipos numéricos y opciones de select.
"""
import io
import logging
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_any_authenticated, get_dependency_user
from app.models.form import Form, FormStatus
from app.models.template import Template
from app.models.user import User

router = APIRouter(tags=["Formularios Excel"])
logger = logging.getLogger(__name__)


def _get_openpyxl():
    try:
        import openpyxl
        return openpyxl
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="openpyxl no está instalado. Ejecute: pip install openpyxl",
        ) from e


def _get_fields(template: Template) -> list[dict]:
    """
    Retorna la lista de campos del template.
    Soporta tanto {"fields": [...]} como {"campos": [...]}.
    Excluye campos de tipo 'computed' (se calculan automáticamente).
    """
    cfg = template.configuracion_campos or {}
    fields = cfg.get("fields") or cfg.get("campos") or []
    return [f for f in fields if f.get("type", f.get("tipo", "text")) != "computed"]


def _field_type(f: dict) -> str:
    """Obtiene el tipo normalizado del campo (acepta 'type' o 'tipo')."""
    return str(f.get("type", f.get("tipo", "text"))).lower()


def _field_label(f: dict) -> str:
    return str(f.get("label", f.get("name", ""))).strip()


def _field_name(f: dict) -> str:
    return str(f.get("name", "")).strip()


def _is_readonly(f: dict) -> bool:
    return bool(f.get("readonly", f.get("bloqueado", False)))


def _is_required(f: dict) -> bool:
    return bool(f.get("required", f.get("requerido", False)))


# ── GET /templates/{template_id}/excel-example ───────────────────────────────

@router.get("/templates/{template_id}/excel-example")
async def download_excel_example(
    template_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Descarga un Excel de ejemplo para el template.
    Incluye todos los campos editables + informe_cualitativo.
    Fila 1: Encabezados con color.
    Fila 2: Tipo de dato esperado (guía).
    Fila 3: Ejemplo de valores.
    """
    openpyxl = _get_openpyxl()
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.activo == True)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    fields = _get_fields(template)

    # Columnas a exportar: campos editables + informe_cualitativo al final
    # Los campos readonly se incluyen solo como referencia pero marcados en gris
    export_cols: list[dict] = []
    for f in fields:
        export_cols.append(f)

    # Agregar informe_cualitativo si no está ya en los campos
    has_informe = any(_field_name(f) == "informe_cualitativo" for f in fields)
    if not has_informe:
        export_cols.append({
            "name": "informe_cualitativo",
            "label": "Informe cualitativo de la búsqueda",
            "type": "textarea",
            "readonly": False,
            "required": True,
            "default": None,
        })

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (template.codigo or template.nombre)[:31]

    # ── Estilos ──────────────────────────────────────────────────────────────
    header_fill    = PatternFill(start_color="1A3C5E", end_color="1A3C5E", fill_type="solid")
    required_fill  = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")  # verde claro
    optional_fill  = PatternFill(start_color="FFF8E1", end_color="FFF8E1", fill_type="solid")  # amarillo claro
    readonly_fill  = PatternFill(start_color="EEEEEE", end_color="EEEEEE", fill_type="solid")  # gris
    type_row_fill  = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")  # azul muy claro

    header_font  = Font(color="FFFFFF", bold=True, size=10, name="Calibri")
    type_font    = Font(color="1A3C5E", italic=True, size=9, name="Calibri")
    normal_font  = Font(size=10, name="Calibri")
    req_font     = Font(color="1B5E20", size=10, name="Calibri")
    opt_font     = Font(color="5D4037", size=10, name="Calibri")
    ro_font      = Font(color="757575", size=10, name="Calibri")

    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC'),
    )

    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align   = Alignment(horizontal="left",   vertical="center", wrap_text=True)

    # ── Fila 1: Encabezados ───────────────────────────────────────────────────
    headers = [_field_label(f) for f in export_cols]
    ws.append(headers)

    # ── Fila 2: Tipo de dato / guía ────────────────────────────────────────
    type_hints = []
    for f in export_cols:
        ft = _field_type(f)
        ro = _is_readonly(f)
        req = _is_required(f)

        if ro:
            hint = "Solo lectura"
        elif ft == "number":
            hint = "Número"
        elif ft == "date":
            hint = "Fecha (AAAA-MM-DD)"
        elif ft == "select":
            opts = f.get("options") or []
            opts_str = " / ".join(str(o.get("value", o) if isinstance(o, dict) else o) for o in opts[:5])
            hint = f"Opciones: {opts_str}" if opts_str else "Seleccionar"
        elif ft == "textarea":
            hint = "Texto largo"
        else:
            hint = "Texto"

        if not ro:
            hint = ("* " if req else "") + hint
        type_hints.append(hint)
    ws.append(type_hints)

    # ── Fila 3: Ejemplo de valores ────────────────────────────────────────
    sample_row = []
    for f in export_cols:
        ft = _field_type(f)
        default = f.get("default")
        if _is_readonly(f):
            sample_row.append(str(default) if default is not None else "")
        elif ft == "date":
            sample_row.append(date.today().isoformat())
        elif ft == "number":
            sample_row.append(0)
        elif ft == "select":
            opts = f.get("options") or []
            if opts:
                first = opts[0]
                sample_row.append(first.get("value", first) if isinstance(first, dict) else first)
            else:
                sample_row.append("")
        elif _field_name(f) == "informe_cualitativo":
            sample_row.append("Descripción detallada de los hallazgos y procesos de búsqueda.")
        else:
            sample_row.append(str(default) if default is not None else "Ejemplo de valor")
    ws.append(sample_row)

    # ── Aplicar estilos columna por columna ───────────────────────────────
    for col_idx, f in enumerate(export_cols, start=1):
        col_letter = get_column_letter(col_idx)
        ro = _is_readonly(f)
        req = _is_required(f)

        # Ancho de columna
        ws.column_dimensions[col_letter].width = 28

        # Fila 1: header
        h_cell = ws.cell(row=1, column=col_idx)
        h_cell.font = header_font
        h_cell.fill = header_fill
        h_cell.alignment = center_align
        h_cell.border = thin_border

        # Fila 2: tipo
        t_cell = ws.cell(row=2, column=col_idx)
        t_cell.font = type_font
        t_cell.fill = type_row_fill
        t_cell.alignment = left_align
        t_cell.border = thin_border

        # Fila 3: ejemplo
        s_cell = ws.cell(row=3, column=col_idx)
        if ro:
            s_cell.fill = readonly_fill
            s_cell.font = ro_font
        elif req:
            s_cell.fill = required_fill
            s_cell.font = req_font
        else:
            s_cell.fill = optional_fill
            s_cell.font = opt_font
        s_cell.alignment = left_align
        s_cell.border = thin_border

    # ── Fila de leyenda ────────────────────────────────────────────────────
    ws.append([""])
    ws.append(["LEYENDA:",
               "Verde = campo requerido (*)",
               "Amarillo = campo opcional",
               "Gris = solo lectura (no editar)",
               "* El símbolo * en la fila de tipo indica campo obligatorio"])
    legend_row = ws.max_row
    legend_cell = ws.cell(row=legend_row, column=1)
    legend_cell.font = Font(bold=True, size=9, color="444444", name="Calibri")
    for col in range(2, 6):
        c = ws.cell(row=legend_row, column=col)
        c.font = Font(size=9, color="666666", name="Calibri")

    # ── Fijar encabezados y zoom ──────────────────────────────────────────
    ws.freeze_panes = "A4"
    ws.row_dimensions[1].height = 32
    ws.row_dimensions[2].height = 28
    ws.row_dimensions[3].height = 24
    ws.sheet_view.zoomScale = 110

    # ── Hoja de referencia ────────────────────────────────────────────────
    ws_ref = wb.create_sheet("Referencia")
    ws_ref.append(["Campo", "Nombre interno", "Tipo", "Requerido", "Solo lectura", "Opciones válidas"])
    ref_header_font = Font(bold=True, color="FFFFFF", size=10)
    ref_header_fill = PatternFill(start_color="37474F", end_color="37474F", fill_type="solid")
    for cell in ws_ref[1]:
        cell.font = ref_header_font
        cell.fill = ref_header_fill
        cell.alignment = center_align

    for f in export_cols:
        opts = f.get("options") or []
        opts_str = ", ".join(str(o.get("value", o) if isinstance(o, dict) else o) for o in opts)
        ws_ref.append([
            _field_label(f),
            _field_name(f),
            _field_type(f),
            "Sí" if _is_required(f) else "No",
            "Sí" if _is_readonly(f) else "No",
            opts_str,
        ])
    for col in ["A", "B", "C", "D", "E", "F"]:
        ws_ref.column_dimensions[col].width = 30

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"plantilla_{template.codigo or str(template_id)}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── POST /forms/upload-excel/{template_id} ───────────────────────────────────

@router.post(
    "/forms/upload-excel/{template_id}",
    status_code=status.HTTP_201_CREATED,
)
async def upload_excel_forms(
    template_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Carga un Excel con múltiples filas y crea formularios en estado draft.

    Validaciones por fila:
    - Campos requeridos no vacíos
    - Campos numéricos parseable como float
    - Campos select con valor dentro de las opciones permitidas
    - informe_cualitativo obligatorio

    Si hay errores retorna 422 con detalle por fila.
    """
    openpyxl = _get_openpyxl()

    # Validar tipo MIME
    allowed_types = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
        "application/zip",  # algunos sistemas envían .xlsx como zip
    }
    if file.content_type not in allowed_types and not (file.filename or "").endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos Excel (.xlsx / .xls)",
        )

    # Cargar template
    t_result = await db.execute(
        select(Template).where(Template.id == template_id, Template.activo == True)
    )
    template = t_result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    all_fields = _get_fields(template)

    # Campos disponibles por label y por name
    field_by_label: dict[str, dict] = {_field_label(f): f for f in all_fields}
    field_by_name:  dict[str, dict] = {_field_name(f): f  for f in all_fields}

    # informe_cualitativo puede no estar en los campos del template
    INFORME_LABEL = "Informe cualitativo de la búsqueda"

    # Leer Excel
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer el archivo Excel: {e}",
        )

    all_rows = list(ws.iter_rows(values_only=True))

    # Debe tener al menos fila 1 (headers) + fila 3 (datos) — saltamos fila 2 (tipo/guía)
    if len(all_rows) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener al menos la fila de encabezados y una fila de datos.",
        )

    header_row = all_rows[0]
    headers = [str(h).strip() if h is not None else "" for h in header_row]

    # Detectar si fila 2 es la fila de tipo/guía (no datos reales)
    # La detectamos si la segunda fila contiene "Número", "Texto", "Fecha", "Solo lectura" etc.
    data_start = 1
    if len(all_rows) >= 2:
        row2_values = [str(v).strip().lower() if v is not None else "" for v in all_rows[1]]
        type_hint_keywords = {"número", "texto", "fecha", "opciones", "solo lectura", "texto largo", "seleccionar"}
        if any(any(kw in v for kw in type_hint_keywords) for v in row2_values if v):
            data_start = 2  # saltar fila de tipo/guía

    data_rows = all_rows[data_start:]

    # Mapear columnas del Excel → campo del template
    # col_map: índice_columna → field_dict (o None para informe_cualitativo)
    col_map: dict[int, dict | str] = {}
    informe_col: int | None = None

    for col_idx, header in enumerate(headers):
        h = header.strip()
        if not h:
            continue
        # informe_cualitativo puede venir por label exacto o por name
        if h == INFORME_LABEL or h == "informe_cualitativo":
            informe_col = col_idx
            continue
        if h in field_by_label:
            col_map[col_idx] = field_by_label[h]
        elif h in field_by_name:
            col_map[col_idx] = field_by_name[h]

    # ── Validar todas las filas antes de crear nada ───────────────────────
    validation_errors: list[dict] = []

    def _cell_val(row: tuple, idx: int) -> Any:
        if idx >= len(row):
            return None
        v = row[idx]
        return v

    def _str_val(v: Any) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        # Eliminar "None" literal que a veces genera openpyxl
        return "" if s.lower() == "none" else s

    for row_idx, row in enumerate(data_rows, start=1):
        # Saltar filas de leyenda / completamente vacías
        non_empty = [c for c in row if c is not None and str(c).strip() not in ("", "None")]
        if not non_empty:
            continue

        # Detectar filas de leyenda por palabra clave
        first_val = _str_val(row[0] if row else None).lower()
        if first_val in {"leyenda:", "nota:", "nota"} or first_val.startswith("leyenda"):
            continue

        row_errors: list[str] = []

        # Validar informe_cualitativo
        informe_val = ""
        if informe_col is not None:
            informe_val = _str_val(_cell_val(row, informe_col))
        if not informe_val:
            row_errors.append("'Informe cualitativo de la búsqueda' es obligatorio")

        # Validar campos mapeados
        for col_idx, field_def in col_map.items():
            if not isinstance(field_def, dict):
                continue
            raw = _cell_val(row, col_idx)
            val = _str_val(raw)
            fname = _field_name(field_def)
            flabel = _field_label(field_def)
            ftype = _field_type(field_def)
            readonly = _is_readonly(field_def)
            required = _is_required(field_def)

            if readonly:
                continue  # no validar solo-lectura

            # Requerido
            if required and not val:
                row_errors.append(f"El campo '{flabel}' es obligatorio")
                continue

            if not val:
                continue  # campo vacío y no requerido — OK

            # Tipo numérico
            if ftype == "number":
                try:
                    float(str(raw).replace(",", "."))
                except (TypeError, ValueError):
                    row_errors.append(f"El campo '{flabel}' debe ser un número (se encontró: '{val}')")

            # Tipo fecha
            elif ftype == "date":
                from datetime import datetime as _dt
                parsed_ok = False
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                    try:
                        _dt.strptime(val[:10], fmt)
                        parsed_ok = True
                        break
                    except ValueError:
                        continue
                if not parsed_ok:
                    # openpyxl puede retornar un date/datetime object
                    import datetime
                    if not isinstance(raw, (datetime.date, datetime.datetime)):
                        row_errors.append(
                            f"El campo '{flabel}' debe ser una fecha (AAAA-MM-DD). Se encontró: '{val}'"
                        )

            # Tipo select
            elif ftype == "select":
                opts = field_def.get("options") or []
                valid_values = set()
                for o in opts:
                    if isinstance(o, dict):
                        valid_values.add(str(o.get("value", "")).strip().lower())
                        valid_values.add(str(o.get("label", "")).strip().lower())
                    else:
                        valid_values.add(str(o).strip().lower())

                if valid_values and val.lower() not in valid_values:
                    opts_display = ", ".join(
                        str(o.get("value", o) if isinstance(o, dict) else o) for o in opts
                    )
                    row_errors.append(
                        f"El campo '{flabel}' tiene un valor inválido ('{val}'). "
                        f"Valores aceptados: {opts_display}"
                    )

        if row_errors:
            validation_errors.append({
                "fila": row_idx + data_start,  # número real en el Excel (1-indexed, + encabezados)
                "errores": row_errors,
            })

    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Se encontraron errores en {len(validation_errors)} fila(s). "
                           "Corrígelos y vuelve a cargar el archivo.",
                "errores_por_fila": validation_errors,
            },
        )

    # ── Crear formularios (todas las filas son válidas) ───────────────────
    created_ids: list[str] = []

    for row in data_rows:
        non_empty = [c for c in row if c is not None and str(c).strip() not in ("", "None")]
        if not non_empty:
            continue
        first_val = _str_val(row[0] if row else None).lower()
        if first_val in {"leyenda:", "nota:", "nota"} or first_val.startswith("leyenda"):
            continue

        datos_dinamicos: dict = {}
        informe_val = ""
        fecha_usuario: date | None = None

        # informe_cualitativo
        if informe_col is not None:
            informe_val = _str_val(_cell_val(row, informe_col))

        for col_idx, field_def in col_map.items():
            if not isinstance(field_def, dict):
                continue
            raw = _cell_val(row, col_idx)
            val = _str_val(raw)
            fname = _field_name(field_def)
            ftype = _field_type(field_def)
            readonly = _is_readonly(field_def)

            if fname == "informe_cualitativo":
                informe_val = val
                continue

            if fname == "mes_reporte" or fname == "fecha_referencia":
                if raw is not None:
                    import datetime
                    if isinstance(raw, (datetime.date, datetime.datetime)):
                        fecha_usuario = raw.date() if isinstance(raw, datetime.datetime) else raw
                    elif val:
                        from datetime import datetime as _dt
                        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                            try:
                                fecha_usuario = _dt.strptime(val[:10], fmt).date()
                                break
                            except ValueError:
                                continue
                continue

            if ftype == "computed":
                continue

            if not val and readonly and field_def.get("default") is not None:
                datos_dinamicos[fname] = field_def["default"]
            elif ftype == "number" and val:
                try:
                    datos_dinamicos[fname] = float(str(raw).replace(",", "."))
                except (TypeError, ValueError):
                    datos_dinamicos[fname] = None
            elif ftype == "date" and raw is not None:
                import datetime
                if isinstance(raw, (datetime.date, datetime.datetime)):
                    datos_dinamicos[fname] = raw.isoformat() if isinstance(raw, datetime.date) else raw.date().isoformat()
                else:
                    datos_dinamicos[fname] = val or None
            else:
                datos_dinamicos[fname] = val or None

        # Rellenar defaults de campos readonly no presentes en el Excel
        for f in all_fields:
            fname = _field_name(f)
            if _is_readonly(f) and f.get("default") is not None:
                datos_dinamicos.setdefault(fname, f["default"])

        form = Form(
            plantilla_id=template_id,
            usuario_id=current_user.id,
            dependency_id=current_user.dependency_id,
            datos_dinamicos=datos_dinamicos,
            informe_cualitativo=informe_val or None,
            fecha_usuario=fecha_usuario or date.today(),
            estado=FormStatus.draft,
            cargado_via_excel=True,
        )
        db.add(form)
        await db.flush()
        created_ids.append(str(form.id))

    if not created_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no contiene filas de datos válidas.",
        )

    await db.commit()

    return {
        "created": len(created_ids),
        "form_ids": created_ids,
        "mensaje": f"Se crearon {len(created_ids)} formulario(s) en estado borrador correctamente.",
    }


# ── GET /forms/{form_id}/excel ────────────────────────────────────────────────

@router.get("/forms/{form_id}/excel")
async def download_form_as_excel(
    form_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Descarga un formulario individual como archivo Excel."""
    openpyxl = _get_openpyxl()
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    form_result = await db.execute(select(Form).where(Form.id == form_id))
    form = form_result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")

    template_result = await db.execute(
        select(Template).where(Template.id == form.plantilla_id)
    )
    template = template_result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    all_fields = _get_fields(template)
    has_informe = any(_field_name(f) == "informe_cualitativo" for f in all_fields)
    export_cols = list(all_fields)
    if not has_informe:
        export_cols.append({
            "name": "informe_cualitativo",
            "label": "Informe cualitativo de la búsqueda",
            "type": "textarea",
            "readonly": False,
            "required": True,
        })

    datos = form.datos_dinamicos or {}

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = (template.codigo or template.nombre)[:31]

    header_fill   = PatternFill(start_color="1A3C5E", end_color="1A3C5E", fill_type="solid")
    readonly_fill = PatternFill(start_color="EEEEEE", end_color="EEEEEE", fill_type="solid")
    data_fill     = PatternFill(start_color="F8FDF8", end_color="F8FDF8", fill_type="solid")
    header_font   = Font(color="FFFFFF", bold=True, size=10, name="Calibri")
    data_font     = Font(size=10, name="Calibri")

    ws.append([_field_label(f) for f in export_cols])
    data_row = []
    for f in export_cols:
        fname = _field_name(f)
        ftype = _field_type(f)
        if fname == "informe_cualitativo":
            data_row.append(form.informe_cualitativo or "")
        elif fname in ("mes_reporte", "fecha_referencia"):
            data_row.append(str(form.fecha_usuario) if form.fecha_usuario else "")
        else:
            data_row.append(datos.get(fname, ""))
    ws.append(data_row)

    for col_idx, f in enumerate(export_cols, start=1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = 28
        h_cell = ws.cell(row=1, column=col_idx)
        h_cell.font = header_font
        h_cell.fill = header_fill
        h_cell.alignment = Alignment(horizontal="center", wrap_text=True)
        d_cell = ws.cell(row=2, column=col_idx)
        d_cell.font = data_font
        d_cell.fill = readonly_fill if _is_readonly(f) else data_fill
        d_cell.alignment = Alignment(horizontal="left", wrap_text=True)

    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"formulario_{form_id}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
