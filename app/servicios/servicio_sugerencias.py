"""Caso de uso de la bandeja de sugerencias.

Centraliza la lectura, persistencia y descarte. El bot no conoce Mongo ni
puede modificar una sugerencia sin pasar el usuario propietario.
"""

from __future__ import annotations

from datetime import UTC, datetime, time

from app.dominio.pendiente import Pendiente
from app.dominio.sugerencia import EstadoSugerencia, Sugerencia
from app.puertos.pendientes_repository import PendientesRepository
from app.puertos.sugerencias_repository import SugerenciasRepository


class ServicioSugerencias:
    """Gestiona sugerencias sin convertirlas todavía en pendientes reales."""

    def __init__(
        self,
        repositorio: SugerenciasRepository,
        pendientes: PendientesRepository,
    ) -> None:
        self._repositorio = repositorio
        self._pendientes = pendientes

    async def guardar_detectadas(
        self,
        usuario_id: str,
        sugerencias: list[Sugerencia],
        detectadas_en: datetime,
    ) -> None:
        """Persiste solo sugerencias nuevas de una detección."""
        await self._repositorio.guardar_nuevas(
            usuario_id,
            sugerencias,
            detectadas_en,
        )

    async def pendientes(self, usuario_id: str) -> list[Sugerencia]:
        """Devuelve la bandeja pendiente del usuario."""
        return await self._repositorio.listar_pendientes(usuario_id)

    async def descartar(
        self,
        sugerencia_id: str,
        usuario_id: str,
    ) -> bool:
        """Descarta una sugerencia propia para que no vuelva a aparecer."""
        return await self._repositorio.cambiar_estado(
            sugerencia_id,
            usuario_id,
            EstadoSugerencia.DESCARTADA,
        )

    async def aceptar(
        self,
        sugerencia_id: str,
        usuario_id: str,
    ) -> Pendiente | None:
        """Convierte una sugerencia propia pendiente en un pendiente confirmado."""
        sugerencia = await self._repositorio.obtener(sugerencia_id, usuario_id)
        if sugerencia is None:
            return None

        vence = (
            datetime.combine(sugerencia.fecha, time.min, tzinfo=UTC) if sugerencia.fecha else None
        )
        pendiente = await self._pendientes.guardar(
            usuario_id,
            sugerencia.texto,
            vence,
        )

        aceptada = await self._repositorio.cambiar_estado(
            sugerencia_id,
            usuario_id,
            EstadoSugerencia.ACEPTADA,
        )
        if aceptada:
            return pendiente

        await self._pendientes.borrar(pendiente.id, usuario_id)
        return None
