"""Cliente Mongo compartido por proceso para no agotar Atlas."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import AsyncMongoClient

TIMEOUT_SELECCION_MS = 5000
MAX_CONEXIONES_POR_PROCESO = 10


@lru_cache(maxsize=4)
def obtener_cliente_mongo(uri: str, *, tz_aware: bool = False) -> AsyncMongoClient[Any]:
    """Reutiliza un pool acotado para todos los adaptadores del proceso."""
    return AsyncMongoClient(
        uri,
        tz_aware=tz_aware,
        serverSelectionTimeoutMS=TIMEOUT_SELECCION_MS,
        connectTimeoutMS=TIMEOUT_SELECCION_MS,
        maxPoolSize=MAX_CONEXIONES_POR_PROCESO,
    )
