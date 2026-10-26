"""Memoria de chat en MongoDB, aislada por usuario y conversación.

Adapta la memoria aportada por Julián a la regla de aislamiento de OT-05.
Retiene los últimos 40 turnos y Mongo elimina documentos tras 30 días sin
actividad. No almacena adjuntos, agenda ni credenciales.
"""

from __future__ import annotations

import logging
from typing import Any

from app.adaptadores.cliente_mongo import obtener_cliente_mongo
from app.dominio.conversacion import MemoriaNoDisponibleError, Turno

logger = logging.getLogger(__name__)

# Por defecto pymongo espera 30 s antes de rendirse si no alcanza el servidor, y el
# bot esperaba ese tiempo en CADA mensaje mientras Atlas rechazaba la IP de la VM.
# 5 s: suficiente para una red sana, y un Mongo caido se nota rapido y degrada.
TIMEOUT_SELECCION_MS = 5000


class MemoriaMongo:
    def __init__(
        self,
        uri: str,
        base: str = "brujula",
        coleccion: str = "conversaciones",
        max_guardados: int = 40,
        ttl_dias: int = 30,
        *,
        _coleccion: Any = None,
    ) -> None:
        self._uri = uri
        self._base = base
        self._nombre_coleccion = coleccion
        self._max = max_guardados
        self._ttl_segundos = ttl_dias * 86400
        self._coleccion_prueba = _coleccion
        self._cliente: Any = None
        self._indice_listo = False

    def _col(self) -> Any:
        if self._coleccion_prueba is not None:
            return self._coleccion_prueba
        if not self._uri:
            raise MemoriaNoDisponibleError("MONGODB_URI no configurado")
        if self._cliente is None:
            self._cliente = obtener_cliente_mongo(self._uri, tz_aware=True)
        return self._cliente[self._base][self._nombre_coleccion]

    async def _asegurar_indices(self, col: Any) -> None:
        if self._indice_listo:
            return
        await col.create_index([("usuario_id", 1), ("conversacion_id", 1)], unique=True)
        await col.create_index("actualizado", expireAfterSeconds=self._ttl_segundos)
        self._indice_listo = True

    async def turnos(self, usuario_id: str, conversacion_id: str, limite: int) -> list[Turno]:
        if limite <= 0:
            return []
        try:
            col = self._col()
            await self._asegurar_indices(col)
            doc = await col.find_one(
                {"usuario_id": usuario_id, "conversacion_id": conversacion_id},
                {"turnos": {"$slice": -limite}},
            )
        except Exception as error:
            logger.warning("No se pudo leer la memoria: %s", type(error).__name__)
            raise MemoriaNoDisponibleError("lectura fallida") from error
        if not doc:
            return []
        return [Turno(t["rol"], t["texto"], t["momento"]) for t in doc.get("turnos", [])]

    async def agregar(self, usuario_id: str, conversacion_id: str, nuevos: list[Turno]) -> None:
        if not nuevos:
            return
        try:
            col = self._col()
            await self._asegurar_indices(col)
            await col.update_one(
                {"usuario_id": usuario_id, "conversacion_id": conversacion_id},
                {
                    "$push": {
                        "turnos": {
                            "$each": [
                                {"rol": t.rol, "texto": t.texto, "momento": t.momento}
                                for t in nuevos
                            ],
                            "$slice": -self._max,
                        }
                    },
                    "$set": {"actualizado": nuevos[-1].momento},
                },
                upsert=True,
            )
        except Exception as error:
            logger.warning("No se pudo guardar la memoria: %s", type(error).__name__)
            raise MemoriaNoDisponibleError("escritura fallida") from error

    async def olvidar(self, usuario_id: str, conversacion_id: str) -> None:
        try:
            col = self._col()
            await col.delete_one({"usuario_id": usuario_id, "conversacion_id": conversacion_id})
        except Exception as error:
            logger.warning("No se pudo borrar la memoria: %s", type(error).__name__)
            raise MemoriaNoDisponibleError("borrado fallido") from error
