"""Adaptador Mongo de sugerencias inferidas.

Guarda únicamente la reformulación del modelo y su trazabilidad. El cuerpo
original del mensaje de Teams nunca llega a esta colección.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, time
from typing import Any

from app.adaptadores.cliente_mongo import obtener_cliente_mongo
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.dominio.sugerencia import DeQuien, EstadoSugerencia, Sugerencia

logger = logging.getLogger(__name__)

NOMBRE = "sugerencias"
_BD = "brujula"
_COLECCION = "sugerencias"
TIMEOUT_SELECCION_MS = 5000


class SugerenciasMongo:
    """Implementa la bandeja persistente y aislada de cada usuario."""

    def __init__(
        self,
        config: Configuracion,
        *,
        _coleccion: Any = None,
    ) -> None:
        self._uri = config.mongodb_uri
        self._coleccion_prueba = _coleccion
        self._cliente: Any = None

    async def guardar_nuevas(
        self,
        usuario_id: str,
        sugerencias: list[Sugerencia],
        detectadas_en: datetime,
    ) -> None:
        if not usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "usuario no identificado")

        coleccion = self._get_coleccion()
        try:
            for sugerencia in sugerencias:
                filtro = {
                    "usuario_id": usuario_id,
                    "id_mensaje": sugerencia.id_mensaje,
                    "texto": sugerencia.texto,
                }
                await coleccion.update_one(
                    filtro,
                    {"$setOnInsert": self._a_documento(sugerencia, usuario_id, detectadas_en)},
                    upsert=True,
                )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al guardar sugerencias en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

    async def listar_pendientes(self, usuario_id: str) -> list[Sugerencia]:
        if not usuario_id:
            return []

        coleccion = self._get_coleccion()
        try:
            cursor = coleccion.find(
                {
                    "usuario_id": usuario_id,
                    "estado": EstadoSugerencia.PENDIENTE,
                }
            )
            documentos = await cursor.to_list()
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al listar sugerencias en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

        return [self._a_sugerencia(documento) for documento in documentos]

    async def obtener(
        self,
        sugerencia_id: str,
        usuario_id: str,
    ) -> Sugerencia | None:
        filtro = self._filtro_seguro(sugerencia_id, usuario_id)
        if filtro is None:
            return None

        coleccion = self._get_coleccion()
        try:
            documento = await coleccion.find_one(
                {
                    **filtro,
                    "estado": EstadoSugerencia.PENDIENTE,
                }
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al consultar sugerencia en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

        return self._a_sugerencia(documento) if documento else None

    async def cambiar_estado(
        self,
        sugerencia_id: str,
        usuario_id: str,
        estado: EstadoSugerencia,
    ) -> bool:
        filtro = self._filtro_seguro(sugerencia_id, usuario_id)
        if filtro is None:
            return False

        coleccion = self._get_coleccion()
        try:
            resultado = await coleccion.update_one(
                {
                    **filtro,
                    "estado": EstadoSugerencia.PENDIENTE,
                },
                {"$set": {"estado": estado}},
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al actualizar sugerencia en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

        return bool(resultado.matched_count)

    @staticmethod
    def _a_documento(
        sugerencia: Sugerencia,
        usuario_id: str,
        detectadas_en: datetime,
    ) -> dict[str, Any]:
        fecha = (
            datetime.combine(sugerencia.fecha, time.min, tzinfo=UTC) if sugerencia.fecha else None
        )
        return {
            "usuario_id": usuario_id,
            "texto": sugerencia.texto,
            "fecha": fecha,
            "confianza": sugerencia.confianza,
            "id_mensaje": sugerencia.id_mensaje,
            "url_mensaje": sugerencia.url_mensaje,
            "chat_nombre": sugerencia.conversacion,
            "de_quien": sugerencia.de_quien,
            "estado": sugerencia.estado,
            "detectada_en": detectadas_en,
        }

    @staticmethod
    def _a_sugerencia(documento: dict[str, Any]) -> Sugerencia:
        fecha_guardada = documento.get("fecha")
        fecha = fecha_guardada.date() if isinstance(fecha_guardada, datetime) else None

        return Sugerencia(
            id=str(documento["_id"]),
            texto=documento["texto"],
            fecha=fecha,
            confianza=float(documento["confianza"]),
            id_mensaje=documento["id_mensaje"],
            url_mensaje=documento["url_mensaje"],
            conversacion=documento["chat_nombre"],
            de_quien=DeQuien(documento["de_quien"]),
            estado=EstadoSugerencia(documento["estado"]),
        )

    @staticmethod
    def _filtro_seguro(
        sugerencia_id: str,
        usuario_id: str,
    ) -> dict[str, Any] | None:
        from bson import ObjectId

        if not usuario_id or not ObjectId.is_valid(sugerencia_id):
            return None

        return {
            "_id": ObjectId(sugerencia_id),
            "usuario_id": usuario_id,
        }

    def _get_coleccion(self) -> Any:
        if self._coleccion_prueba is not None:
            return self._coleccion_prueba
        if not self._uri:
            raise FuenteNoDisponibleError(NOMBRE, "MONGODB_URI no configurado")
        if self._cliente is None:
            self._cliente = obtener_cliente_mongo(self._uri)
        return self._cliente[_BD][_COLECCION]
