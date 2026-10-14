"""Adaptador secundario: MongoDB para pendientes propios del usuario.

Primera fuente de Brujula que NO es de Microsoft. Implementa dos puertos:
  - TaskSource (lectura): FuentePropiaMongo.obtener_pendientes
  - PendientesRepository (escritura): FuentePropiaMongo.guardar

El cliente se construye perezosamente: sin MONGODB_URI la aplicacion
arranca igual y esta fuente reporta FuenteNoDisponibleError cuando se le
consulta. Una fuente opcional no puede ser requisito de arranque (el mismo
principio que GeminiProvider con GEMINI_API_KEY).

AISLAMIENTO ENTRE USUARIOS: toda consulta y escritura filtra por
usuario_id (AAD Object ID). Un find({}) sin filtro viola OWASP A01.
El test de aislamiento en test_mongo_pendientes.py verifica esto de forma
automatica y debe pasar siempre.

Dependencia: pymongo>=4.9 con AsyncMongoClient (motor es end-of-life desde
14-may-2026). El import es perezoso para que pytest funcione sin MONGODB_URI.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.dominio.pendiente import FuentePendiente, Pendiente

logger = logging.getLogger(__name__)

NOMBRE = "pendientes propios"
_BD = "brujula"
_COLECCION = "pendientes"
# Por defecto pymongo espera 30 s antes de rendirse si no alcanza el servidor, y el
# bot esperaba ese tiempo en CADA mensaje mientras Atlas rechazaba la IP de la VM.
# 5 s: suficiente para una red sana, y un Mongo caido se nota rapido y degrada.
TIMEOUT_SELECCION_MS = 5000
_URL_FALLBACK = "https://teams.microsoft.com"


def _url_bot(config: Configuracion) -> str:
    """Enlace profundo al chat con el bot. Siempre una URL valida."""
    if config.teams_bot_id:
        return f"https://teams.microsoft.com/l/chat/0/0?users=28:{config.teams_bot_id}"
    return _URL_FALLBACK


def _filtro_pendiente_usuario(
    pendiente_id: str,
    usuario_id: str,
) -> dict[str, Any] | None:
    """Construye un filtro seguro para modificar solo pendientes propios."""
    from bson import ObjectId

    id_mongo = pendiente_id.removeprefix("propio-")
    if not usuario_id or not ObjectId.is_valid(id_mongo):
        return None

    return {
        "_id": ObjectId(id_mongo),
        "usuario_id": usuario_id,
    }


class FuentePropiaMongo:
    """Pendientes creados por el usuario dentro de Brujula, en MongoDB.

    Implementa TaskSource (lectura) y PendientesRepository (escritura)
    sin importar ninguno de los dos puertos: tipado estructural de Python.
    El composition root (composicion.py) sabe que esta clase cumple los
    dos contratos y la pasa a quien corresponde.
    """

    def __init__(
        self,
        config: Configuracion,
        usuario_id: str,
        *,
        _coleccion: Any = None,
    ) -> None:
        self._uri = config.mongodb_uri
        self._usuario_id = usuario_id
        self._url_bot = _url_bot(config)
        self._coleccion_prueba = _coleccion  # inyectado solo en tests
        self._cliente: Any = None

    @property
    def nombre(self) -> str:
        return NOMBRE

    # --- TaskSource (lectura) -------------------------------------------

    async def obtener_pendientes(self, desde: datetime, hasta: datetime) -> list[Pendiente]:
        if not self._usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "usuario no identificado")

        col = self._get_coleccion()
        try:
            # Sin fecha siempre entra; con fecha solo si cae en la ventana.
            filtro: dict[str, Any] = {
                "usuario_id": self._usuario_id,
                "completado": False,
                "$or": [
                    {"vence": None},
                    {"vence": {"$gte": desde, "$lte": hasta}},
                ],
            }
            cursor = col.find(filtro)
            docs = await cursor.to_list()
        except FuenteNoDisponibleError:
            raise
        except Exception as e:
            logger.exception("Error al consultar MongoDB: %s", e)
            raise FuenteNoDisponibleError(NOMBRE, str(e)) from e

        return [self._a_pendiente(doc) for doc in docs]

    # --- PendientesRepository (escritura) --------------------------------

    async def guardar(
        self,
        usuario_id: str,
        titulo: str,
        vence: datetime | None,
    ) -> Pendiente:
        if not usuario_id:
            raise FuenteNoDisponibleError(NOMBRE, "usuario no identificado")

        col = self._get_coleccion()
        doc: dict[str, Any] = {
            "usuario_id": usuario_id,
            "titulo": titulo,
            "vence": vence,
            "completado": False,
            "creado_en": datetime.now(UTC),
        }
        try:
            result = await col.insert_one(doc)
        except FuenteNoDisponibleError:
            raise
        except Exception as e:
            logger.exception("Error al guardar en MongoDB: %s", e)
            raise FuenteNoDisponibleError(NOMBRE, str(e)) from e

        return Pendiente(
            id=f"propio-{result.inserted_id}",
            titulo=titulo,
            fuente=FuentePendiente.PROPIO,
            url_origen=self._url_bot,
            vence=vence,
            confianza=1.0,
        )

    async def completar(self, pendiente_id: str, usuario_id: str) -> bool:
        filtro = _filtro_pendiente_usuario(pendiente_id, usuario_id)
        if filtro is None:
            return False

        col = self._get_coleccion()
        try:
            result = await col.update_one(
                filtro,
                {"$set": {"completado": True}},
            )
        except FuenteNoDisponibleError:
            raise
        except Exception as e:
            logger.exception("Error al completar pendiente en MongoDB: %s", e)
            raise FuenteNoDisponibleError(NOMBRE, str(e)) from e

        return bool(result.matched_count)

    async def borrar(self, pendiente_id: str, usuario_id: str) -> bool:
        filtro = _filtro_pendiente_usuario(pendiente_id, usuario_id)
        if filtro is None:
            return False

        col = self._get_coleccion()
        try:
            result = await col.delete_one(filtro)
        except FuenteNoDisponibleError:
            raise
        except Exception as e:
            logger.exception("Error al borrar pendiente en MongoDB: %s", e)
            raise FuenteNoDisponibleError(NOMBRE, str(e)) from e

        return bool(result.deleted_count)

    # --- Internos --------------------------------------------------------

    def _get_coleccion(self) -> Any:
        """Devuelve la coleccion de MongoDB. Perezoso: falla si no hay URI."""
        if self._coleccion_prueba is not None:
            return self._coleccion_prueba
        if not self._uri:
            raise FuenteNoDisponibleError(NOMBRE, "MONGODB_URI no configurado")
        if self._cliente is None:
            from pymongo import AsyncMongoClient  # import perezoso

            self._cliente = AsyncMongoClient(
                self._uri,
                serverSelectionTimeoutMS=TIMEOUT_SELECCION_MS,
                connectTimeoutMS=TIMEOUT_SELECCION_MS,
            )
        return self._cliente[_BD][_COLECCION]

    def _a_pendiente(self, doc: dict[str, Any]) -> Pendiente:
        return Pendiente(
            id=f"propio-{doc['_id']}",
            titulo=doc["titulo"],
            fuente=FuentePendiente.PROPIO,
            url_origen=self._url_bot,
            vence=doc.get("vence"),
            confianza=1.0,
        )
