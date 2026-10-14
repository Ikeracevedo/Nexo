"""Contrato para preferencias persistentes y privadas de cada usuario.

La vigilancia de conversaciones nunca puede depender de memoria del proceso:
un reinicio no debe activarla por accidente ni olvidar que el usuario la apagó.
El servicio conoce este puerto; Mongo será solo su implementación.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class PreferenciasRepository(Protocol):
    """Almacena preferencias aisladas por el AAD Object ID del usuario."""

    async def vigilancia_activa(self, usuario_id: str) -> bool:
        """Devuelve False si el usuario nunca activó la vigilancia."""

    async def activar_vigilancia(self, usuario_id: str, activada_en: datetime) -> None:
        """Activa la vigilancia explícitamente y registra cuándo ocurrió."""

    async def desactivar_vigilancia(self, usuario_id: str) -> None:
        """Apaga la vigilancia sin borrar el registro de preferencia."""

    async def usuarios_con_vigilancia_activa(self) -> list[str]:
        """Lista solo identificadores de usuarios que aceptaron la precarga."""
