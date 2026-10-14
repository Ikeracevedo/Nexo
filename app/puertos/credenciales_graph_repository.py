"""Contrato para credenciales renovables de Graph por usuario."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class CredencialesGraphRepository(Protocol):
    """Expone refresh tokens solo dentro del proceso autorizado."""

    async def guardar_refresh_token(
        self,
        usuario_id: str,
        refresh_token: str,
        actualizado_en: datetime,
    ) -> None:
        """Persiste el refresh token cifrado mediante el adaptador."""

    async def obtener_refresh_token(self, usuario_id: str) -> str | None:
        """Devuelve el token en memoria o None si no existe."""

    async def borrar_credenciales(self, usuario_id: str) -> None:
        """Elimina las credenciales revocadas del usuario."""
