"""Precarga opcional de sugerencias con ventana limitada y sin almacenar chats."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta

from app.dominio.errores import FuenteNoDisponibleError, LLMNoDisponibleError
from app.dominio.precarga import EstadoPrecarga
from app.puertos.credenciales_graph_repository import CredencialesGraphRepository
from app.puertos.estado_precarga_repository import EstadoPrecargaRepository
from app.puertos.fuente_mensajes import FabricaFuenteMensajes, MensajeConversacion
from app.puertos.oauth_graph import RenovadorTokenOAuth
from app.puertos.preferencias_repository import PreferenciasRepository
from app.puertos.sugerencias_repository import SugerenciasRepository
from app.servicios.servicio_deteccion import ServicioDeteccion

logger = logging.getLogger(__name__)

VENTANA_MENSAJES = timedelta(days=7)
INTERVALO_PRE_CARGA = timedelta(minutes=30)
MAX_MENSAJES_POR_ANALISIS = 300


class ServicioPrecarga:
    """Actualiza sugerencias de usuarios que aceptaron la vigilancia explícita."""

    def __init__(
        self,
        preferencias: PreferenciasRepository,
        credenciales: CredencialesGraphRepository,
        renovador: RenovadorTokenOAuth,
        fuentes: FabricaFuenteMensajes,
        detector: ServicioDeteccion,
        sugerencias: SugerenciasRepository,
        estado: EstadoPrecargaRepository,
        intervalo: timedelta = INTERVALO_PRE_CARGA,
    ) -> None:
        self._preferencias = preferencias
        self._credenciales = credenciales
        self._renovador = renovador
        self._fuentes = fuentes
        self._detector = detector
        self._sugerencias = sugerencias
        self._estado = estado
        self._intervalo = intervalo

    async def actualizar_todos(self, ahora: datetime) -> int:
        """Procesa usuarios aislados; un fallo nunca bloquea a los demás."""
        usuarios = await self._preferencias.usuarios_con_vigilancia_activa()
        actualizados = 0
        for usuario_id in usuarios:
            try:
                if await self.actualizar_usuario(usuario_id, ahora):
                    actualizados += 1
            except (FuenteNoDisponibleError, LLMNoDisponibleError) as error:
                logger.warning("Precarga omitida por %s", type(error).__name__)
        return actualizados

    async def actualizar_usuario(self, usuario_id: str, ahora: datetime) -> bool:
        """Procesa solo si venció el intervalo y la huella de mensajes cambió."""
        anterior = await self._estado.obtener(usuario_id)
        if anterior and ahora - anterior.ultima_precarga_en < self._intervalo:
            return False

        refresh_token = await self._credenciales.obtener_refresh_token(usuario_id)
        if refresh_token is None:
            raise FuenteNoDisponibleError(
                "credenciales Graph", "usuario sin autorización renovable"
            )
        tokens = await self._renovador.renovar_refresh_token(refresh_token)
        await self._credenciales.guardar_refresh_token(usuario_id, tokens.refresh_token, ahora)

        mensajes = await self._fuentes.crear(usuario_id, tokens.access_token).mensajes_recientes(
            desde=ahora - VENTANA_MENSAJES,
            tope=MAX_MENSAJES_POR_ANALISIS,
        )
        huella = self._huella(mensajes)
        if anterior and anterior.huella_mensajes == huella:
            await self._estado.guardar(usuario_id, EstadoPrecarga(ahora, huella))
            return False

        detectadas = await self._detector.detectar(mensajes, ahora)
        await self._sugerencias.guardar_nuevas(usuario_id, detectadas, ahora)
        await self._estado.guardar(usuario_id, EstadoPrecarga(ahora, huella))
        return True

    @staticmethod
    def _huella(mensajes: list[MensajeConversacion]) -> str:
        """Resume identificadores y fechas; el contenido nunca participa ni persiste."""
        resumen = "\n".join(
            f"{mensaje.id}:{mensaje.enviado_en.isoformat()}" for mensaje in mensajes
        )
        return hashlib.sha256(resumen.encode("utf-8")).hexdigest()
