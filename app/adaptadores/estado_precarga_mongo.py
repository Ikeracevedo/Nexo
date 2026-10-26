"""Caché Mongo de precargas, deliberadamente libre de cuerpos de mensajes."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.adaptadores.cliente_mongo import obtener_cliente_mongo
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.dominio.precarga import EstadoPrecarga

logger = logging.getLogger(__name__)

NOMBRE = "estado de precarga"
_BD = "brujula"
_COLECCION = "estado_precarga"
TIMEOUT_SELECCION_MS = 5000


class EstadoPrecargaMongo:
    """Guarda frecuencia y huella, no los datos que originaron la huella."""

    def __init__(self, config: Configuracion, *, _coleccion: Any = None) -> None:
        self._uri = config.mongodb_uri
        self._coleccion_prueba = _coleccion
        self._cliente: Any = None

    async def obtener(self, usuario_id: str) -> EstadoPrecarga | None:
        if not usuario_id:
            return None
        try:
            documento = await self._get_coleccion().find_one({"usuario_id": usuario_id})
        except Exception as error:
            logger.exception("Error al leer estado de precarga: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error
        if not documento:
            return None
        fecha = documento.get("ultima_precarga_en")
        huella = documento.get("huella_mensajes")
        if not isinstance(fecha, datetime) or not isinstance(huella, str):
            return None
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=UTC)
        return EstadoPrecarga(fecha, huella)

    async def guardar(self, usuario_id: str, estado: EstadoPrecarga) -> None:
        if not usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "usuario no identificado")
        try:
            await self._get_coleccion().update_one(
                {"usuario_id": usuario_id},
                {
                    "$set": {
                        "ultima_precarga_en": estado.ultima_precarga_en,
                        "huella_mensajes": estado.huella_mensajes,
                    }
                },
                upsert=True,
            )
        except Exception as error:
            logger.exception("Error al guardar estado de precarga: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error

    def _get_coleccion(self) -> Any:
        if self._coleccion_prueba is not None:
            return self._coleccion_prueba
        if not self._uri:
            raise FuenteNoDisponibleError(NOMBRE, "MONGODB_URI no configurado")
        if self._cliente is None:
            self._cliente = obtener_cliente_mongo(self._uri)
        return self._cliente[_BD][_COLECCION]
