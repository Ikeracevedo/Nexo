"""Puerto para estados OAuth temporales y de un solo uso."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class EstadoOAuthRepository(Protocol):
    """Relaciona un retorno OAuth con el usuario que inició la conexión."""

    async def crear(self, estado: str, usuario_id: str, expira_en: datetime) -> None:
        """Guarda un estado aleatorio que podrá consumirse una sola vez."""

    async def consumir(self, estado: str, ahora: datetime) -> str | None:
        """Consume el estado vigente y devuelve su usuario, o ``None``."""
