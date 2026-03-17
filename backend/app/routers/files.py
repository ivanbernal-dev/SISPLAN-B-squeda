"""
app/routers/files.py — Endpoints de gestión de archivos adjuntos (MinIO).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_any_authenticated, get_client_ip, get_dependency_user
from app.models.audit_log import AuditLog
from app.models.file import Archivo
from app.models.form import Form, FormStatus
from app.models.user import User, UserRole
from app.schemas.file import FileResponse, FileUrlResponse
from app.services.minio_service import MinioService, get_minio_service

router = APIRouter(prefix="/files", tags=["Archivos"])


async def _log_audit(db: AsyncSession, **kwargs) -> None:
    db.add(AuditLog(**kwargs))


async def _get_form_or_404(db: AsyncSession, form_id: uuid.UUID) -> Form:
    result = await db.execute(select(Form).where(Form.id == form_id))
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulario no encontrado")
    return form


@router.post(
    "/upload/{form_id}",
    response_model=list[FileResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_files(
    request: Request,
    form_id: uuid.UUID,
    files: list[UploadFile],
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
    minio: MinioService = Depends(get_minio_service),
) -> list[FileResponse]:
    """Sube uno o más archivos a un formulario (almacenado en MinIO)."""
    form = await _get_form_or_404(db, form_id)

    if form.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este formulario")
    if form.estado not in (FormStatus.draft, FormStatus.rejected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden adjuntar archivos a formularios en estado draft o rejected",
        )

    uploaded: list[FileResponse] = []
    for file in files:
        archivo = await minio.upload_file(
            file=file,
            form_id=form_id,
            dep_id=form.dependency_id,
        )
        db.add(archivo)
        await db.flush()

        await _log_audit(
            db,
            usuario_id=current_user.id,
            accion="FILE_UPLOAD",
            entidad_tipo="archivo",
            entidad_id=archivo.id,
            detalle={
                "formulario_id": str(form_id),
                "nombre_original": archivo.nombre_original,
            },
            ip_address=get_client_ip(request),
        )
        uploaded.append(FileResponse.model_validate(archivo))

    return uploaded


@router.get("/{file_id}/url", response_model=FileUrlResponse)
async def get_file_url(
    file_id: uuid.UUID,
    current_user: User = Depends(get_any_authenticated),
    db: AsyncSession = Depends(get_db),
    minio: MinioService = Depends(get_minio_service),
) -> FileUrlResponse:
    """Genera una URL pre-firmada temporal para descargar el archivo."""
    result = await db.execute(select(Archivo).where(Archivo.id == file_id))
    archivo = result.scalar_one_or_none()
    if archivo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    # dependency_user solo puede acceder a archivos de sus propios formularios
    if current_user.role == UserRole.dependency_user:
        form = await _get_form_or_404(db, archivo.formulario_id)
        if form.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este archivo")

    url = minio.get_presigned_url(archivo)
    from app.config import settings
    return FileUrlResponse(
        file_id=archivo.id,
        nombre_original=archivo.nombre_original,
        url=url,
        expires_in_seconds=settings.MINIO_PRESIGNED_URL_EXPIRY,
    )


@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(
    request: Request,
    file_id: uuid.UUID,
    current_user: User = Depends(get_dependency_user),
    db: AsyncSession = Depends(get_db),
    minio: MinioService = Depends(get_minio_service),
) -> dict:
    """Elimina un archivo adjunto (solo en formularios draft o rejected)."""
    result = await db.execute(select(Archivo).where(Archivo.id == file_id))
    archivo = result.scalar_one_or_none()
    if archivo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    form = await _get_form_or_404(db, archivo.formulario_id)
    if form.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este archivo")
    if form.estado not in (FormStatus.draft, FormStatus.rejected):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden eliminar archivos de formularios en estado draft o rejected",
        )

    minio.delete_file(archivo)
    await db.delete(archivo)

    await _log_audit(
        db,
        usuario_id=current_user.id,
        accion="FILE_DELETE",
        entidad_tipo="archivo",
        entidad_id=file_id,
        detalle={"formulario_id": str(archivo.formulario_id)},
        ip_address=get_client_ip(request),
    )
    return {"detail": "Archivo eliminado exitosamente"}
