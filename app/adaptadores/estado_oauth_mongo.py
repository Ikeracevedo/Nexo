"""Estado OAuth efímero persistido en Mongo para sobrevivir a reinicios."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError

logger = logging.getLogger(__name__)

NOMBRE = "estado OAuth"
_BD = "brujula"
_COLECCION = "estados_oauth"
TIMEOUT_SELECCION_MS = 5000


class EstadoOAuthMongo:
    """Implementa estados opacos, vencibles y consumibles una única vez."""

    def __init__(self, config: Configuracion, *, _coleccion: Any = None) -> None:
        self._uri = config.mongodb_uri
        self._coleccion_prueba = _coleccion
        self._cliente: Any = None

    async def crear(self, estado: str, usuario_id: str, expira_en: datetime) -> None:
        if not estado or not usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "estado o usuario no disponible")
        try:
            await self._get_coleccion().insert_one(
                {
                    "estado": estado,
                    "usuario_id": usuario_id,
                    "expira_en": expira_en,
                    "usado": False,
                }
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al guardar estado OAuth: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error

    async def consumir(self, estado: str, ahora: datetime) -> str | None:
        if not estado:
            return None
        try:
            documento = await self._get_coleccion().find_one_and_update(
                {"estado": estado, "usado": False, "expira_en": {"$gt": ahora}},
                {"$set": {"usado": True, "consumido_en": ahora}},
                return_document=True,
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al consumir estado OAuth: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error

        usuario_id = documento.get("usuario_id") if documento else None
        return usuario_id if isinstance(usuario_id, str) else None

    def _get_coleccion(self) -> Any:
        if self._coleccion_prueba is not None:
            return self._coleccion_prueba
        if not self._uri:
            raise FuenteNoDisponibleError(NOMBRE, "MONGODB_URI no configurado")
        if self._cliente is None:
            from pymongo import AsyncMongoClient

            self._cliente = AsyncMongoClient(
                self._uri,
                serverSelectionTimeoutMS=TIMEOUT_SELECCION_MS,
                connectTimeoutMS=TIMEOUT_SELECCION_MS,
            )
        return self._cliente[_BD][_COLECCION]
