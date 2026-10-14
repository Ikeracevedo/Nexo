"""Almacén cifrado de refresh tokens delegados para el worker.

Mongo conserva solamente `refresh_token_cifrado`; el valor legible se descifra
en memoria, se usa para renovar Graph y se descarta al terminar la operación.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.seguridad.cifrado import CifradorTokens

logger = logging.getLogger(__name__)

NOMBRE = "credenciales de Graph"
_BD = "brujula"
_COLECCION = "credenciales_graph"
TIMEOUT_SELECCION_MS = 5000


class CredencialesGraphMongo:
    """Implementa credenciales renovables, cifradas y aisladas por usuario."""

    def __init__(
        self,
        config: Configuracion,
        *,
        _coleccion: Any = None,
    ) -> None:
        self._uri = config.mongodb_uri
        self._cifrador = CifradorTokens(config.brujula_token_encryption_key)
        self._coleccion_prueba = _coleccion
        self._cliente: Any = None

    async def guardar_refresh_token(
        self,
        usuario_id: str,
        refresh_token: str,
        actualizado_en: datetime,
    ) -> None:
        if not usuario_id or not refresh_token:
            raise FuenteNoDisponibleError(NOMBRE, "usuario o token no disponible")

        coleccion = self._get_coleccion()
        try:
            await coleccion.update_one(
                {"usuario_id": usuario_id},
                {
                    "$set": {
                        "refresh_token_cifrado": self._cifrador.cifrar(refresh_token),
                        "actualizado_en": actualizado_en,
                    }
                },
                upsert=True,
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al guardar credenciales de Graph: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error

    async def obtener_refresh_token(self, usuario_id: str) -> str | None:
        if not usuario_id:
            return None

        coleccion = self._get_coleccion()
        try:
            documento = await coleccion.find_one({"usuario_id": usuario_id})
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al leer credenciales de Graph: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error

        if not documento:
            return None

        token_cifrado = documento.get("refresh_token_cifrado")
        if not isinstance(token_cifrado, str):
            return None

        return self._cifrador.descifrar(token_cifrado)

    async def borrar_credenciales(self, usuario_id: str) -> None:
        if not usuario_id:
            return

        coleccion = self._get_coleccion()
        try:
            await coleccion.delete_one({"usuario_id": usuario_id})
        except FuenteNoDisponibleError:
            raise
        except Exception as error:
            logger.exception("Error al borrar credenciales de Graph: %s", error)
            raise FuenteNoDisponibleError(NOMBRE, type(error).__name__) from error

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
