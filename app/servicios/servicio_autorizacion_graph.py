"""Caso de uso para conectar Graph con autorización renovable por usuario."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from app.config import Configuracion
from app.dominio.errores import ConfiguracionInvalidaError, FuenteNoDisponibleError
from app.puertos.credenciales_graph_repository import CredencialesGraphRepository
from app.puertos.estado_oauth_repository import EstadoOAuthRepository
from app.puertos.oauth_graph import IntercambiadorCodigoOAuth
from app.puertos.preferencias_repository import PreferenciasRepository

_DURACION_ESTADO = timedelta(minutes=10)
_SCOPES = (
    "openid profile offline_access User.Read Chat.Read Chat.ReadBasic "
    "Calendars.Read Tasks.Read Group.Read.All"
)


class ServicioAutorizacionGraph:
    """Crea enlaces OAuth y guarda solo tokens cifrados del usuario correcto."""

    def __init__(
        self,
        config: Configuracion,
        estados: EstadoOAuthRepository,
        intercambiador: IntercambiadorCodigoOAuth,
        credenciales: CredencialesGraphRepository,
        preferencias: PreferenciasRepository,
    ) -> None:
        self._config = config
        self._estados = estados
        self._intercambiador = intercambiador
        self._credenciales = credenciales
        self._preferencias = preferencias

    async def crear_enlace(self, usuario_id: str, ahora: datetime) -> str:
        self._validar_configuracion()
        estado = secrets.token_urlsafe(32)
        await self._estados.crear(estado, usuario_id, ahora + _DURACION_ESTADO)
        parametros = urlencode(
            {
                "client_id": self._config.azure_client_id,
                "response_type": "code",
                "redirect_uri": self._config.azure_redirect_uri,
                "response_mode": "query",
                "scope": _SCOPES,
                "state": estado,
            }
        )
        return (
            f"https://login.microsoftonline.com/{self._config.azure_tenant_id}"
            f"/oauth2/v2.0/authorize?{parametros}"
        )

    async def completar(self, estado: str, codigo: str, ahora: datetime) -> None:
        usuario_id = await self._estados.consumir(estado, ahora)
        if usuario_id is None:
            raise FuenteNoDisponibleError(
                "autorización Graph", "estado inválido, vencido o ya usado"
            )
        credenciales = await self._intercambiador.intercambiar_codigo(codigo)
        if credenciales.usuario_id != usuario_id:
            raise FuenteNoDisponibleError("autorización Graph", "la cuenta autorizada no coincide")
        await self._credenciales.guardar_refresh_token(
            usuario_id,
            credenciales.refresh_token,
            ahora,
        )
        await self._preferencias.activar_vigilancia(usuario_id, ahora)

    def _validar_configuracion(self) -> None:
        if not self._config.azure_tenant_id or not self._config.azure_client_id:
            raise ConfiguracionInvalidaError("AZURE_TENANT_ID y AZURE_CLIENT_ID son obligatorios")
        if not self._config.azure_redirect_uri.startswith("https://"):
            raise ConfiguracionInvalidaError("AZURE_REDIRECT_URI debe usar HTTPS en producción")
