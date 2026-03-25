"""
app/routers/forms_excel.py — Endpoints para carga y descarga de formularios via Excel.

Requires: openpyxl (add to requirements.txt if not present)
"""
import io
import logging
import uuid
from datetime import date

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


# ── GET /templates/{template_id}/excel-example ───────────────────────────────

@router.get("/templates/{template_id}/excel-example")
async def download_excel_example(
    template_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Descarga un archivo Excel de ejemplo para el template dado.
    Contiene una fila de encabezados y una fila de ejemplo con los valores por defecto.
    """
    openpyxl = _get_openpyxl()

    result = await db.execute(
        select(Template).where(Template.id == template_id, Template.activo == True)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    fields = template.configuracion_campos.get("fields", [])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = template.codigo or template.nombre[:31]

    # Header row
    headers = [f.get("label", f.get("name", "")) for f in fields]
    ws.append(headers)

    # Sample row with defaults (skip file fields)
    sample_row = []
    for f in fields:
        tipo = f.get("tipo", "text")
        if tipo == "file":
            sample_row.append("")
        elif f.get("default") is not None:
            sample_row.append(f["default"])
        elif tipo == "date":
            sample_row.append(date.today().isoformat())
        elif tipo == "number":
            sample_row.append(0)
        else:
            sample_row.append("")
    ws.append(sample_row)

    # Style header row
    from openpyxl.styles import Font, PatternFill, Alignment
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=10)

    readonly_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    editable_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    for col_idx, (field, header_cell) in enumerate(zip(fields, ws[1]), start=1):
        header_cell.font = header_font
        header_cell.fill = header_fill
        header_cell.alignment = Alignment(wrap_text=True)
        ws.column_dimensions[header_cell.column_letter].width = 20

        # Color sample row based on readonly
        sample_cell = ws.cell(row=2, column=col_idx)
        if field.get("readonly"):
            sample_cell.fill = readonly_fill
        else:
            sample_cell.fill = editable_fill

    # Add a notes row
    ws.append([""])
    notes_row_idx = 3
    note_cell = ws.cell(row=notes_row_idx, column=1)
    note_cell.value = "NOTA: Las celdas en gris son de solo lectura. Las celdas en verde deben llenarse."

    # Freeze header row
    ws.freeze_panes = "A2"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"ejemplo_{template.codigo or template_id}.xlsx"
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
    Carga un archivo Excel con múltiples filas y crea un formulario en estado draft
    por cada fila de datos (omitiendo la fila de encabezados).

    Returns: {"created": N, "form_ids": [...]}
    """
    openpyxl = _get_openpyxl()

    if file.content_type not in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos Excel (.xlsx)",
        )

    # Load template
    t_result = await db.execute(
        select(Template).where(Template.id == template_id, Template.activo == True)
    )
    template = t_result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template no encontrado")

    fields = template.configuracion_campos.get("fields", [])
    field_by_label = {f.get("label", f.get("name", "")): f for f in fields}
    field_by_name = {f["name"]: f for f in fields}

    # Read Excel
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo leer el archivo Excel: {e}",
        )

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe tener al menos una fila de encabezados y una de datos.",
        )

    # Map header labels to column index
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    col_map: dict[str, int] = {}  # field_name → column_index
    for col_idx, header in enumerate(headers):
        if header in field_by_label:
            field_def = field_by_label[header]
            col_map[field_def["name"]] = col_idx
        elif header in field_by_name:
            col_map[header] = col_idx

    created_ids = []

    for row in rows[1:]:
        # Skip completely empty rows
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        datos_dinamicos: dict = {}
        informe_cualitativo = ""
        fecha_usuario: date | None = None

        for field_name, col_idx in col_map.items():
            if col_idx >= len(row):
                continue
            raw_value = row[col_idx]
            field_def = field_by_name.get(field_name, {})
            tipo = field_def.get("tipo", "text")

            # Handle special fields
            if field_name == "informe_cualitativo":
                informe_cualitativo = str(raw_value) if raw_value is not None else ""
                continue
            if field_name == "mes_reporte":
                if raw_value:
                    if isinstance(raw_value, (date,)):
                        fecha_usuario = raw_value
                    else:
                        try:
                            from datetime import datetime as dt
                            parsed = dt.strptime(str(raw_value)[:10], "%Y-%m-%d").date()
                            fecha_usuario = parsed
                        except (ValueError, TypeError):
                            fecha_usuario = date.today()
                continue
            if tipo == "file":
                continue

            # Convert value by type
            if raw_value is None:
                datos_dinamicos[field_name] = None
            elif tipo == "number":
                try:
                    datos_dinamicos[field_name] = float(raw_value)
                except (TypeError, ValueError):
                    datos_dinamicos[field_name] = None
            else:
                datos_dinamicos[field_name] = str(raw_value) if raw_value != "" else None

        # Fill readonly defaults
        for f in fields:
            if f.get("readonly") and f.get("default") is not None:
                datos_dinamicos.setdefault(f["name"], f["default"])

        form = Form(
            plantilla_id=template_id,
            usuario_id=current_user.id,
            dependency_id=current_user.dependency_id,
            datos_dinamicos=datos_dinamicos,
            informe_cualitativo=informe_cualitativo or None,
            fecha_usuario=fecha_usuario or date.today(),
            estado=FormStatus.draft,
            cargado_via_excel=True,
        )
        db.add(form)
        await db.flush()
        created_ids.append(str(form.id))

    await db.commit()

    return {
        "created": len(created_ids),
        "form_ids": created_ids,
        "mensaje": f"Se crearon {len(created_ids)} formularios en estado borrador.",
    }


# ── GET /forms/{form_id}/excel ────────────────────────────────────────────────

@router.get("/forms/{form_id}/excel")
async def download_form_as_excel(
    form_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Descarga un formulario individual como archivo Excel.
    """
    openpyxl = _get_openpyxl()

    form_result = await db.execute(select(Form).where(Form.id == form_id))
    form = form_result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")

    template_result = await db.execute(
        select(Template).where(Template.id == form.plantilla_id)
    )
    template = template_result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template del formulario no encontrado")

    fields = template.configuracion_campos.get("fields", [])
    datos = form.datos_dinamicos or {}

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = template.codigo or template.nombre[:31]

    from openpyxl.styles import Font, PatternFill, Alignment
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=10)
    readonly_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    editable_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    # Header row
    headers = [f.get("label", f.get("name", "")) for f in fields]
    ws.append(headers)

    # Data row
    data_row = []
    for f in fields:
        tipo = f.get("tipo", "text")
        name = f.get("name", "")
        if name == "informe_cualitativo":
            data_row.append(form.informe_cualitativo or "")
        elif name == "mes_reporte":
            data_row.append(str(form.fecha_usuario) if form.fecha_usuario else "")
        elif tipo == "file":
            data_row.append("[ver archivos adjuntos]")
        else:
            data_row.append(datos.get(name, ""))
    ws.append(data_row)

    # Style
    for col_idx, (field, header_cell) in enumerate(zip(fields, ws[1]), start=1):
        header_cell.font = header_font
        header_cell.fill = header_fill
        header_cell.alignment = Alignment(wrap_text=True)
        ws.column_dimensions[header_cell.column_letter].width = 22

        data_cell = ws.cell(row=2, column=col_idx)
        if field.get("readonly"):
            data_cell.fill = readonly_fill
        else:
            data_cell.fill = editable_fill

    # Metadata sheet
    ws_meta = wb.create_sheet("Metadata")
    ws_meta.append(["Campo", "Valor"])
    ws_meta.append(["ID Formulario", str(form.id)])
    ws_meta.append(["Template", template.nombre])
    ws_meta.append(["Estado", form.estado.value])
    ws_meta.append(["Fecha carga", str(form.fecha_carga)])
    ws_meta.append(["Cargado via Excel", str(form.cargado_via_excel)])

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
