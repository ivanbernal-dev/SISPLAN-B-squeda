"""
app/routers/admin_backup.py — Backup & restore completo de la base de datos.

Endpoints expuestos bajo /admin/backup:
    GET  /export-zip   → descarga un ZIP con todos los templates, forms y archivos
    POST /import-zip   → restaura un ZIP previamente exportado (upsert por id)
    POST /wipe         → limpia toda la base (registros y/o templates), bajo confirmación

Layout del ZIP:
    backup_manifest.json    versión + fecha + conteos
    templates.json          todos los templates (todas las columnas)
    forms.json              todos los formularios (datos_dinamicos incluido)
    archivos.json           metadata de cada archivo
    files/<archivo_id>/<nombre_original>   bytes crudos
"""
from __future__ import annotations

import io
import json
import logging
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form as FastForm, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_admin_user, get_client_ip
from app.models.audit_log import AuditLog
from app.models.file import Archivo
from app.models.form import Form, FormStatus
from app.models.template import Template
from app.models.user import User
from app.services.minio_service import get_minio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/backup", tags=["Administración"])

BACKUP_VERSION = 1
WIPE_CONFIRM_TOKEN = "BORRAR TODO"


def _iso(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        s = str(value)
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _template_to_dict(t: Template) -> dict:
    return {
        "id": str(t.id),
        "nombre": t.nombre,
        "codigo": t.codigo,
        "descripcion": t.descripcion,
        "indicador_nivel1_id": t.indicador_nivel1_id,
        "indicador_nivel2_id": t.indicador_nivel2_id,
        "codigo_markdown": t.codigo_markdown,
        "configuracion_campos": t.configuracion_campos,
        "version": t.version,
        "activo": t.activo,
        "created_at": _iso(t.created_at),
        "updated_at": _iso(t.updated_at),
    }


def _form_to_dict(f: Form) -> dict:
    return {
        "id": str(f.id),
        "plantilla_id": str(f.plantilla_id),
        "dependency_id": str(f.dependency_id) if f.dependency_id else None,
        "usuario_id": str(f.usuario_id) if f.usuario_id else None,
        "estado": f.estado.value if hasattr(f.estado, "value") else str(f.estado),
        "fecha_usuario": _iso(f.fecha_usuario),
        "fecha_carga": _iso(f.fecha_carga),
        "fecha_edicion": _iso(f.fecha_edicion),
        "fecha_validacion": _iso(f.fecha_validacion),
        "informe_cualitativo": f.informe_cualitativo,
        "datos_dinamicos": f.datos_dinamicos,
        "comentario_rechazo": f.comentario_rechazo,
        "cargado_via_excel": f.cargado_via_excel,
        "lote_excel_id": f.lote_excel_id,
        "validado_por_id": str(f.validado_por_id) if f.validado_por_id else None,
    }


def _archivo_to_dict(a: Archivo) -> dict:
    return {
        "id": str(a.id),
        "formulario_id": str(a.formulario_id),
        "nombre_original": a.nombre_original,
        "nombre_minio": a.nombre_minio,
        "bucket": a.bucket,
        "ruta_minio": a.ruta_minio,
        "tipo_mime": a.tipo_mime,
        "tamano_bytes": a.tamaño_bytes,
        "uploaded_at": _iso(a.uploaded_at),
    }


# ════════════════════════════════════════════════════════════════════════════════
#                                  EXPORT
# ════════════════════════════════════════════════════════════════════════════════

@router.get("/export-zip")
async def export_full_backup(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Descarga un ZIP con todos los templates + formularios + archivos."""
    tpls = (await db.execute(select(Template).order_by(Template.codigo))).scalars().all()
    forms = (await db.execute(select(Form).order_by(Form.fecha_carga))).scalars().all()
    archivos = (await db.execute(select(Archivo))).scalars().all()

    manifest = {
        "version": BACKUP_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": current_user.email or current_user.username,
        "counts": {
            "templates": len(tpls),
            "forms": len(forms),
            "archivos": len(archivos),
        },
    }

    zip_buf = io.BytesIO()
    minio = get_minio_service()
    archivos_ok = 0
    archivos_fail: list[dict] = []

    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr(
            "templates.json",
            json.dumps([_template_to_dict(t) for t in tpls], ensure_ascii=False, indent=2, default=str),
        )
        zf.writestr(
            "forms.json",
            json.dumps([_form_to_dict(f) for f in forms], ensure_ascii=False, indent=2, default=str),
        )
        zf.writestr(
            "archivos.json",
            json.dumps([_archivo_to_dict(a) for a in archivos], ensure_ascii=False, indent=2, default=str),
        )

        for a in archivos:
            try:
                resp = minio.get_file_stream(a)
                try:
                    data = resp.read()
                finally:
                    try:
                        resp.close()
                        resp.release_conn()
                    except Exception:
                        pass
                safe_name = (a.nombre_original or a.nombre_minio or "archivo").replace("/", "_")
                zf.writestr(f"files/{a.id}/{safe_name}", data)
                archivos_ok += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Backup: no se pudo leer archivo %s: %s", a.id, exc)
                archivos_fail.append({"id": str(a.id), "error": str(exc)})

        if archivos_fail:
            zf.writestr(
                "_files_omitidos.json",
                json.dumps(archivos_fail, ensure_ascii=False, indent=2),
            )

    zip_buf.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"ubpd_backup_{ts}.zip"
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-Templates": str(len(tpls)),
            "X-Backup-Forms": str(len(forms)),
            "X-Backup-Archivos-OK": str(archivos_ok),
            "X-Backup-Archivos-Fail": str(len(archivos_fail)),
        },
    )


# ════════════════════════════════════════════════════════════════════════════════
#                                  IMPORT
# ════════════════════════════════════════════════════════════════════════════════

@router.post("/import-zip")
async def import_full_backup(
    request: Request,
    file: UploadFile = File(..., description="ZIP exportado por /admin/backup/export-zip"),
    replace: bool = FastForm(False),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Restaura un backup previo. Upsert por id.

    Si replace=true, vacía formularios + archivos + templates antes de cargar.
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail=f"ZIP inválido: {exc}") from exc

    names = set(zf.namelist())
    for required in ("backup_manifest.json", "templates.json", "forms.json", "archivos.json"):
        if required not in names:
            raise HTTPException(
                status_code=400,
                detail=f"El ZIP no contiene '{required}'. ¿Es un backup generado por este sistema?",
            )

    manifest = json.loads(zf.read("backup_manifest.json").decode("utf-8"))
    tpls_data = json.loads(zf.read("templates.json").decode("utf-8"))
    forms_data = json.loads(zf.read("forms.json").decode("utf-8"))
    archivos_data = json.loads(zf.read("archivos.json").decode("utf-8"))

    minio = get_minio_service()

    deleted_before = {"forms": 0, "archivos": 0, "templates": 0}
    if replace:
        existing_archivos = (await db.execute(select(Archivo))).scalars().all()
        for a in existing_archivos:
            try:
                minio.delete_file(a)
            except Exception as exc:  # noqa: BLE001
                logger.warning("wipe-archivo %s: %s", a.id, exc)
        result_arch = await db.execute(sa_delete(Archivo))
        deleted_before["archivos"] = result_arch.rowcount or 0
        result_forms = await db.execute(sa_delete(Form))
        deleted_before["forms"] = result_forms.rowcount or 0
        result_tpls = await db.execute(sa_delete(Template))
        deleted_before["templates"] = result_tpls.rowcount or 0
        await db.flush()

    # ── Upsert TEMPLATES ────────────────────────────────────────────────────
    tpl_created = tpl_updated = 0
    existing_tpls = {str(t.id): t for t in (await db.execute(select(Template))).scalars().all()}
    existing_by_codigo = {t.codigo: t for t in existing_tpls.values() if t.codigo}

    for item in tpls_data:
        tid = item.get("id")
        tpl = existing_tpls.get(tid) if tid else None
        if tpl is None and item.get("codigo"):
            tpl = existing_by_codigo.get(item["codigo"])
        if tpl is None:
            tpl = Template(
                id=uuid.UUID(tid) if tid else uuid.uuid4(),
                nombre=item.get("nombre") or "Sin nombre",
                codigo=item.get("codigo"),
                descripcion=item.get("descripcion"),
                indicador_nivel1_id=item.get("indicador_nivel1_id"),
                indicador_nivel2_id=item.get("indicador_nivel2_id"),
                codigo_markdown=item.get("codigo_markdown") or "",
                configuracion_campos=item.get("configuracion_campos") or {},
                version=item.get("version") or 1,
                activo=bool(item.get("activo", True)),
            )
            db.add(tpl)
            tpl_created += 1
        else:
            tpl.nombre = item.get("nombre") or tpl.nombre
            tpl.codigo = item.get("codigo") or tpl.codigo
            tpl.descripcion = item.get("descripcion")
            if item.get("indicador_nivel1_id") is not None:
                tpl.indicador_nivel1_id = item["indicador_nivel1_id"]
            if item.get("indicador_nivel2_id") is not None:
                tpl.indicador_nivel2_id = item["indicador_nivel2_id"]
            if item.get("codigo_markdown") is not None:
                tpl.codigo_markdown = item["codigo_markdown"]
            if item.get("configuracion_campos") is not None:
                tpl.configuracion_campos = item["configuracion_campos"]
            if item.get("version"):
                tpl.version = item["version"]
            if item.get("activo") is not None:
                tpl.activo = bool(item["activo"])
            tpl_updated += 1

    await db.flush()
    existing_tpls = {str(t.id): t for t in (await db.execute(select(Template))).scalars().all()}

    # ── Upsert FORMS ────────────────────────────────────────────────────────
    form_created = form_updated = form_skipped = 0
    existing_forms = {str(f.id): f for f in (await db.execute(select(Form))).scalars().all()}

    for item in forms_data:
        fid = item.get("id")
        plantilla_id = item.get("plantilla_id")
        if not plantilla_id or plantilla_id not in existing_tpls:
            form_skipped += 1
            continue
        form = existing_forms.get(fid) if fid else None
        estado_raw = (item.get("estado") or "draft").lower()
        try:
            estado_enum = FormStatus(estado_raw)
        except ValueError:
            estado_enum = FormStatus.draft

        try:
            dep_uuid = uuid.UUID(item["dependency_id"]) if item.get("dependency_id") else None
            usr_uuid = uuid.UUID(item["usuario_id"]) if item.get("usuario_id") else None
        except (ValueError, TypeError):
            form_skipped += 1
            continue

        if form is None:
            form = Form(
                id=uuid.UUID(fid) if fid else uuid.uuid4(),
                plantilla_id=uuid.UUID(plantilla_id),
                dependency_id=dep_uuid,
                usuario_id=usr_uuid,
                estado=estado_enum,
                fecha_usuario=_parse_iso(item.get("fecha_usuario")),
                fecha_carga=_parse_iso(item.get("fecha_carga")) or datetime.now(timezone.utc),
                informe_cualitativo=item.get("informe_cualitativo"),
                datos_dinamicos=item.get("datos_dinamicos") or {},
                comentario_rechazo=item.get("comentario_rechazo"),
                cargado_via_excel=bool(item.get("cargado_via_excel", False)),
                lote_excel_id=item.get("lote_excel_id"),
            )
            if item.get("fecha_validacion"):
                form.fecha_validacion = _parse_iso(item["fecha_validacion"])
            if item.get("validado_por_id"):
                try:
                    form.validado_por_id = uuid.UUID(item["validado_por_id"])
                except (ValueError, TypeError):
                    pass
            db.add(form)
            form_created += 1
        else:
            form.estado = estado_enum
            form.datos_dinamicos = item.get("datos_dinamicos") or {}
            form.informe_cualitativo = item.get("informe_cualitativo")
            if item.get("fecha_usuario"):
                form.fecha_usuario = _parse_iso(item["fecha_usuario"])
            if item.get("fecha_validacion"):
                form.fecha_validacion = _parse_iso(item["fecha_validacion"])
            form_updated += 1

    await db.flush()
    existing_forms = {str(f.id): f for f in (await db.execute(select(Form))).scalars().all()}

    # ── Upsert ARCHIVOS + subir bytes a MinIO ───────────────────────────────
    arch_created = arch_updated = arch_skipped = 0
    arch_minio_ok = arch_minio_fail = 0
    existing_arch = {str(a.id): a for a in (await db.execute(select(Archivo))).scalars().all()}

    for item in archivos_data:
        aid = item.get("id")
        form_id = item.get("formulario_id") or item.get("form_id")
        if not form_id or form_id not in existing_forms:
            arch_skipped += 1
            continue
        arch = existing_arch.get(aid) if aid else None
        if arch is None:
            arch = Archivo(
                id=uuid.UUID(aid) if aid else uuid.uuid4(),
                formulario_id=uuid.UUID(form_id),
                nombre_original=item.get("nombre_original") or "archivo",
                nombre_minio=item.get("nombre_minio") or "",
                bucket=item.get("bucket") or minio.bucket,
                ruta_minio=item.get("ruta_minio") or "",
                tipo_mime=item.get("tipo_mime") or item.get("mime_type"),
            )
            arch.tamaño_bytes = item.get("tamano_bytes") or item.get("tamaño_bytes")
            db.add(arch)
            arch_created += 1
        else:
            arch.nombre_original = item.get("nombre_original") or arch.nombre_original
            arch.nombre_minio = item.get("nombre_minio") or arch.nombre_minio
            arch.bucket = item.get("bucket") or arch.bucket
            arch.ruta_minio = item.get("ruta_minio") or arch.ruta_minio
            arch.tipo_mime = item.get("tipo_mime") or item.get("mime_type") or arch.tipo_mime
            new_size = item.get("tamano_bytes") or item.get("tamaño_bytes")
            if new_size is not None:
                arch.tamaño_bytes = new_size
            arch_updated += 1

        # Subir bytes a MinIO si vienen en el ZIP — siempre vía put_object directo
        safe_name = (item.get("nombre_original") or "archivo").replace("/", "_")
        candidate_path = f"files/{aid}/{safe_name}"
        if candidate_path in names and arch.ruta_minio:
            try:
                blob = zf.read(candidate_path)
                minio.client.put_object(
                    bucket_name=arch.bucket or minio.bucket,
                    object_name=arch.ruta_minio,
                    data=io.BytesIO(blob),
                    length=len(blob),
                    content_type=arch.tipo_mime or "application/octet-stream",
                )
                arch_minio_ok += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("import-archivo %s: %s", aid, exc)
                arch_minio_fail += 1

    await db.commit()

    db.add(AuditLog(
        accion="BACKUP_RESTORE",
        usuario_id=current_user.id,
        entidad_tipo="backup",
        entidad_id=None,
        detalle={
            "filename": file.filename,
            "replace": replace,
            "manifest": manifest,
            "templates": {"creados": tpl_created, "actualizados": tpl_updated},
            "forms": {"creados": form_created, "actualizados": form_updated, "omitidos": form_skipped},
            "archivos": {
                "creados": arch_created,
                "actualizados": arch_updated,
                "omitidos": arch_skipped,
                "minio_ok": arch_minio_ok,
                "minio_fail": arch_minio_fail,
            },
            "borrados_previos": deleted_before,
        },
        ip_address=get_client_ip(request),
    ))
    await db.commit()

    return {
        "ok": True,
        "replace": replace,
        "manifest": manifest,
        "templates": {"creados": tpl_created, "actualizados": tpl_updated},
        "forms": {"creados": form_created, "actualizados": form_updated, "omitidos": form_skipped},
        "archivos": {
            "creados": arch_created,
            "actualizados": arch_updated,
            "omitidos": arch_skipped,
            "minio_ok": arch_minio_ok,
            "minio_fail": arch_minio_fail,
        },
        "borrados_previos": deleted_before,
    }


# ════════════════════════════════════════════════════════════════════════════════
#                                   WIPE
# ════════════════════════════════════════════════════════════════════════════════

@router.post("/wipe")
async def wipe_database(
    request: Request,
    body: dict,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Limpia formularios + archivos (y opcionalmente templates) tras confirmación.

    Body:
        {
            "confirm_token": "BORRAR TODO",     # obligatorio (texto literal)
            "include_templates": false           # true → borra también templates
        }
    """
    confirm_token = (body or {}).get("confirm_token", "")
    if confirm_token != WIPE_CONFIRM_TOKEN:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Confirmación incorrecta. Para borrar la base, envía "
                f"confirm_token=\"{WIPE_CONFIRM_TOKEN}\" (texto exacto)."
            ),
        )
    include_templates = bool((body or {}).get("include_templates", False))

    minio = get_minio_service()
    archivos = (await db.execute(select(Archivo))).scalars().all()
    minio_ok = minio_fail = 0
    for a in archivos:
        try:
            minio.delete_file(a)
            minio_ok += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("wipe minio %s: %s", a.id, exc)
            minio_fail += 1

    deleted_archivos = (await db.execute(sa_delete(Archivo))).rowcount or 0
    deleted_forms = (await db.execute(sa_delete(Form))).rowcount or 0
    deleted_templates = 0
    if include_templates:
        deleted_templates = (await db.execute(sa_delete(Template))).rowcount or 0
    await db.commit()

    db.add(AuditLog(
        accion="DATABASE_WIPE",
        usuario_id=current_user.id,
        entidad_tipo="backup",
        entidad_id=None,
        detalle={
            "deleted_forms": deleted_forms,
            "deleted_archivos": deleted_archivos,
            "deleted_templates": deleted_templates,
            "include_templates": include_templates,
            "minio_ok": minio_ok,
            "minio_fail": minio_fail,
        },
        ip_address=get_client_ip(request),
    ))
    await db.commit()

    return {
        "ok": True,
        "deleted_forms": deleted_forms,
        "deleted_archivos": deleted_archivos,
        "deleted_templates": deleted_templates,
        "include_templates": include_templates,
        "minio_ok": minio_ok,
        "minio_fail": minio_fail,
    }
