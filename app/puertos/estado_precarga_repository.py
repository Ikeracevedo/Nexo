"""Contrato para la caché privada de precarga de sugerencias."""

from __future__ import annotations

from typing import Protocol

from app.dominio.precarga import EstadoPrecarga


class EstadoPrecargaRepository(Protocol):
    """Persiste solo huellas y tiempos; nunca texto de Teams ni prompts."""

    async def obtener(self, usuario_id: str) -> EstadoPrecarga | None:
        """Devuelve el estado de un usuario, aislado por su AAD Object ID."""

    async def guardar(self, usuario_id: str, estado: EstadoPrecarga) -> None:
        """Actualiza el estado de precarga del usuario indicado."""
