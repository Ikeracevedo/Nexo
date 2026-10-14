"""Contrato de la bandeja de sugerencias, aislada por usuario."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.dominio.sugerencia import EstadoSugerencia, Sugerencia


class SugerenciasRepository(Protocol):
    """Persiste sugerencias sin almacenar el cuerpo original de Teams."""

    async def guardar_nuevas(
        self,
        usuario_id: str,
        sugerencias: list[Sugerencia],
        detectadas_en: datetime,
    ) -> None:
        """Guarda sugerencias inéditas sin revivir una descartada."""

    async def listar_pendientes(self, usuario_id: str) -> list[Sugerencia]:
        """Lista solo sugerencias pendientes del usuario indicado."""

    async def obtener(
        self,
        sugerencia_id: str,
        usuario_id: str,
    ) -> Sugerencia | None:
        """Busca una sugerencia pendiente del usuario indicado."""

    async def cambiar_estado(
        self,
        sugerencia_id: str,
        usuario_id: str,
        estado: EstadoSugerencia,
    ) -> bool:
        """Cambia el estado solo si pertenece al usuario."""
