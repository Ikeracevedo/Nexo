"""Adaptador HTTP para intercambiar códigos OAuth delegados de Entra."""

from __future__ import annotations

import logging

import httpx

from app.config import Configuracion
from app.dominio.errores import ConfiguracionInvalidaError, FuenteNoDisponibleError
from app.puertos.oauth_graph import CredencialesDelegadasGraph, TokensRenovadosGraph

logger = logging.getLogger(__name__)

NOMBRE = "autorización Graph"
_SCOPES = (
    "openid profile offline_access User.Read Chat.Read Chat.ReadBasic "
    "Calendars.Read Tasks.Read Group.Read.All"
)


class IntercambiadorCodigoEntra:
    """Obtiene tokens delegados y valida su propietario mediante ``/me``."""

    def __init__(self, config: Configuracion, *, _cliente: httpx.AsyncClient | None = None) -> None:
        self._config = config
        self._cliente_prueba = _cliente

    async def intercambiar_codigo(self, codigo: str) -> CredencialesDelegadasGraph:
        if not codigo:
            raise FuenteNoDisponibleError(NOMBRE, "código de autorización ausente")
        self._validar_configuracion()
        cliente = self._cliente_prueba or httpx.AsyncClient(timeout=10)
        try:
            respuesta = await cliente.post(
                f"https://login.microsoftonline.com/{self._config.azure_tenant_id}/oauth2/v2.0/token",
                data={
                    "client_id": self._config.azure_client_id,
                    "client_secret": self._config.azure_client_secret,
                    "code": codigo,
                    "redirect_uri": self._config.azure_redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": _SCOPES,
                },
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            access_token = datos["access_token"]
            refresh_token = datos["refresh_token"]
            if not isinstance(access_token, str) or not isinstance(refresh_token, str):
                raise ValueError("respuesta de tokens inválida")
            perfil = await cliente.get(
                "https://graph.microsoft.com/v1.0/me?$select=id",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            perfil.raise_for_status()
            usuario_id = perfil.json()["id"]
            if not isinstance(usuario_id, str) or not usuario_id:
                raise ValueError("perfil de Graph inválido")
            return CredencialesDelegadasGraph(usuario_id, refresh_token)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            logger.warning("Falló el intercambio OAuth de Graph: %s", type(error).__name__)
            raise FuenteNoDisponibleError(NOMBRE, "no se pudo validar la autorización") from error
        finally:
            if self._cliente_prueba is None:
                await cliente.aclose()

    async def renovar_refresh_token(self, refresh_token: str) -> TokensRenovadosGraph:
        """Renueva Graph y conserva la rotación de refresh token de Entra."""
        if not refresh_token:
            raise FuenteNoDisponibleError(NOMBRE, "refresh token ausente")
        self._validar_configuracion()
        cliente = self._cliente_prueba or httpx.AsyncClient(timeout=10)
        try:
            respuesta = await cliente.post(
                f"https://login.microsoftonline.com/{self._config.azure_tenant_id}/oauth2/v2.0/token",
                data={
                    "client_id": self._config.azure_client_id,
                    "client_secret": self._config.azure_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": _SCOPES,
                },
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            access_token = datos["access_token"]
            refresh_actualizado = datos.get("refresh_token", refresh_token)
            if not isinstance(access_token, str) or not isinstance(refresh_actualizado, str):
                raise ValueError("respuesta de renovación inválida")
            return TokensRenovadosGraph(access_token, refresh_actualizado)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            logger.warning("Falló la renovación OAuth de Graph: %s", type(error).__name__)
            raise FuenteNoDisponibleError(NOMBRE, "no se pudo renovar la autorización") from error
        finally:
            if self._cliente_prueba is None:
                await cliente.aclose()

    def _validar_configuracion(self) -> None:
        if not self._config.azure_client_secret:
            raise ConfiguracionInvalidaError("AZURE_CLIENT_SECRET es obligatorio")
