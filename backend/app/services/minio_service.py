"""
app/services/minio_service.py — Servicio de almacenamiento de archivos con MinIO.
"""
import io
import logging
import uuid
from datetime import timedelta

from fastapi import HTTPException, UploadFile, status
from minio import Minio
from minio.error import S3Error

from app.config import settings
from app.models.file import Archivo

logger = logging.getLogger(__name__)


class MinioService:
    """Encapsula todas las operaciones de almacenamiento con MinIO."""

    def __init__(self) -> None:
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Crea el bucket principal si no existe."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info("Bucket '%s' creado en MinIO.", self.bucket)
            else:
                logger.debug("Bucket '%s' ya existe.", self.bucket)
        except S3Error as exc:
            logger.error("Error al verificar/crear bucket MinIO: %s", exc)
            raise

    def _get_object_path(
        self, dep_id: uuid.UUID, form_id: uuid.UUID, filename: str
    ) -> str:
        """Genera la ruta interna del objeto: {dep_id}/{form_id}/{filename}"""
        return f"{dep_id}/{form_id}/{filename}"

    async def upload_file(
        self,
        file: UploadFile,
        form_id: uuid.UUID,
        dep_id: uuid.UUID,
    ) -> Archivo:
        """
        Sube un archivo a MinIO y retorna un objeto Archivo (sin guardar en BD).
        El llamador debe persistir el objeto en la sesión de base de datos.
        """
        # Validar tamaño
        contents = await file.read()
        size = len(contents)
        if size > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"El archivo supera el límite de {settings.MAX_UPLOAD_MB} MB",
            )

        # Validar MIME
        content_type = file.content_type or "application/octet-stream"
        if content_type not in settings.allowed_mime_types_list:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Tipo de archivo no permitido: {content_type}",
            )

        # Nombre único para evitar colisiones
        ext = ""
        if file.filename and "." in file.filename:
            ext = "." + file.filename.rsplit(".", 1)[-1]
        unique_name = f"{uuid.uuid4()}{ext}"
        object_path = self._get_object_path(dep_id, form_id, unique_name)

        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_path,
                data=io.BytesIO(contents),
                length=size,
                content_type=content_type,
            )
        except S3Error as exc:
            logger.error("Error al subir archivo a MinIO: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al almacenar el archivo",
            )

        return Archivo(
            formulario_id=form_id,
            nombre_original=file.filename or unique_name,
            nombre_minio=unique_name,
            bucket=self.bucket,
            ruta_minio=object_path,
            tipo_mime=content_type,
            tamaño_bytes=size,
        )

    def get_presigned_url(self, file_record: Archivo) -> str:
        """Genera una URL pre-firmada con expiración para descargar el archivo."""
        try:
            url = self.client.presigned_get_object(
                bucket_name=file_record.bucket,
                object_name=file_record.ruta_minio,
                expires=timedelta(seconds=settings.MINIO_PRESIGNED_URL_EXPIRY),
            )
            return url
        except S3Error as exc:
            logger.error("Error al generar URL pre-firmada: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al generar URL de descarga",
            )

    def get_file_stream(self, file_record: Archivo):
        """
        Retorna el stream HTTP de un objeto MinIO.
        El llamador es responsable de cerrar la conexión (.close() + .release_conn()).
        """
        try:
            return self.client.get_object(
                bucket_name=file_record.bucket,
                object_name=file_record.ruta_minio,
            )
        except S3Error as exc:
            logger.error("Error al obtener stream de MinIO: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener el archivo",
            )

    def delete_file(self, file_record: Archivo) -> None:
        """Elimina el objeto de MinIO."""
        try:
            self.client.remove_object(
                bucket_name=file_record.bucket,
                object_name=file_record.ruta_minio,
            )
        except S3Error as exc:
            logger.warning("Error al eliminar archivo de MinIO: %s", exc)


# Instancia singleton
minio_service = MinioService.__new__(MinioService)


def get_minio_service() -> MinioService:
    """Dependencia FastAPI que retorna el servicio MinIO inicializado."""
    return minio_service


def init_minio() -> None:
    """Inicializa la instancia singleton de MinIO (llamar al arrancar la app)."""
    global minio_service
    minio_service = MinioService()
