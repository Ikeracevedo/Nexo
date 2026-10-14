"""Contrato para leer mensajes recientes sin convertirlos aún en pendientes.

Los adaptadores devuelven datos brutos en memoria. Detectar compromisos es
responsabilidad de un servicio posterior, no de Microsoft Graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class MensajeConversacion:
    """Mensaje reciente, normalizado para el detector de compromisos."""

    id: str
    texto: str
    autor: str
    es_del_usuario: bool
    enviado_en: datetime
    conversacion: str
    url: str


class FuenteMensajes(Protocol):
    """Origen de mensajes recientes para detectar compromisos bajo demanda."""

    @property
    def nombre(self) -> str: ...

    async def mensajes_recientes(
        self,
        desde: datetime,
        tope: int,
    ) -> list[MensajeConversacion]: ...


class FabricaFuenteMensajes(Protocol):
    """Construye una fuente con el access token renovado de un usuario."""

    def crear(self, usuario_id: str, access_token: str) -> FuenteMensajes: ...
