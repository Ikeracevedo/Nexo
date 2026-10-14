"""Caso de uso del consentimiento explícito para analizar conversaciones.

La vigilancia vive aquí y no en el bot: Teams solo traduce `vigilar` y
`no vigilar`; la decisión de privacidad se puede probar sin SDK ni Mongo.
"""

from __future__ import annotations

from datetime import datetime

from app.puertos.credenciales_graph_repository import CredencialesGraphRepository
from app.puertos.preferencias_repository import PreferenciasRepository

MENSAJE_VIGILANCIA_ACTIVADA = (
    "Voy a leer los mensajes de tus chats de los últimos 7 días para proponerte "
    "compromisos que no tengas anotados. Solo veo lo que tú ya puedes ver. "
    "No guardo el texto de los mensajes: solo el pendiente que te proponga y el "
    "enlace al mensaje. Puedes apagarlo con `no vigilar`."
)

MENSAJE_VIGILANCIA_DESACTIVADA = "La vigilancia está desactivada. Ya no leeré tus conversaciones."


class ServicioVigilancia:
    """Activa y desactiva la vigilancia por decisión explícita del usuario."""

    def __init__(
        self,
        preferencias: PreferenciasRepository,
        credenciales: CredencialesGraphRepository,
    ) -> None:
        self._preferencias = preferencias
        self._credenciales = credenciales

    async def activa(self, usuario_id: str) -> bool:
        """Indica si el usuario autorizó analizar sus conversaciones."""
        return await self._preferencias.vigilancia_activa(usuario_id)

    async def activar(self, usuario_id: str, ahora: datetime) -> str:
        """Guarda el consentimiento y devuelve su explicación completa."""
        await self._preferencias.activar_vigilancia(usuario_id, ahora)
        return MENSAJE_VIGILANCIA_ACTIVADA

    async def desactivar(self, usuario_id: str) -> str:
        """Revoca la vigilancia sin borrar el historial de la preferencia."""
        await self._credenciales.borrar_credenciales(usuario_id)
        await self._preferencias.desactivar_vigilancia(usuario_id)
        return MENSAJE_VIGILANCIA_DESACTIVADA
