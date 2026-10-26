"""Adaptador Mongo para la preferencia de vigilancia de conversaciones.

La ausencia de documento significa vigilancia apagada. Así el estado inicial
es privado por defecto y sobrevive reinicios o múltiples réplicas del bot.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.adaptadores.cliente_mongo import obtener_cliente_mongo
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError

logger = logging.getLogger(__name__)

NOMBRE = "preferencias"
_BD = "brujula"
_COLECCION = "preferencias"
TIMEOUT_SELECCION_MS = 5000


class PreferenciasMongo:
    """Persiste la decisión explícita de cada usuario sobre la vigilancia."""

    def __init__(
        self,
        config: Configuracion,
        *,
        _coleccion: Any = None,
    ) -> None:
        self._uri = config.mongodb_uri
        self._coleccion_prueba = _coleccion
        self._cliente: Any = None

    async def vigilancia_activa(self, usuario_id: str) -> bool:
        if not usuario_id:
            return False

        col = self._get_coleccion()
        try:
            documento = await col.find_one({"usuario_id": usuario_id})
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al leer preferencias en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

        return bool(documento and documento.get("vigilancia_activa"))

    async def activar_vigilancia(self, usuario_id: str, activada_en: datetime) -> None:
        if not usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "usuario no identificado")

        col = self._get_coleccion()
        try:
            await col.update_one(
                {"usuario_id": usuario_id},
                {
                    "$set": {
                        "vigilancia_activa": True,
                        "activada_en": activada_en,
                    }
                },
                upsert=True,
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al activar vigilancia en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

    async def desactivar_vigilancia(self, usuario_id: str) -> None:
        if not usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "usuario no identificado")

        col = self._get_coleccion()
        try:
            await col.update_one(
                {"usuario_id": usuario_id},
                {"$set": {"vigilancia_activa": False}},
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al desactivar vigilancia en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error

    async def usuarios_con_vigilancia_activa(self) -> list[str]:
        """Expone al worker únicamente los IDs con consentimiento vigente."""
        try:
            cursor = self._get_coleccion().find(
                {"vigilancia_activa": True},
                {"usuario_id": 1, "_id": 0},
            )
            documentos = await cursor.to_list()
        except Exception as error:
            logger.exception("Error al listar vigilancia activa en MongoDB: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, str(error)) from error
        return [
            usuario_id
            for documento in documentos
            if isinstance((usuario_id := documento.get("usuario_id")), str) and usuario_id
        ]

    def _get_coleccion(self) -> Any:
        if self._coleccion_prueba is not None:
            return self._coleccion_prueba
        if not self._uri:
            raise FuenteNoDisponibleError(NOMBRE, "MONGODB_URI no configurado")
        if self._cliente is None:
            self._cliente = obtener_cliente_mongo(self._uri)
        return self._cliente[_BD][_COLECCION]
