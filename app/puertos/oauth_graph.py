"""Puertos y datos mínimos para la autorización delegada de Graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CredencialesDelegadasGraph:
    """Resultado validado del intercambio de código con Entra."""

    usuario_id: str
    refresh_token: str


@dataclass(frozen=True)
class TokensRenovadosGraph:
    """Access token efímero y refresh token posiblemente rotado por Entra."""

    access_token: str
    refresh_token: str


class IntercambiadorCodigoOAuth(Protocol):
    """Intercambia un código de autorización por credenciales delegadas."""

    async def intercambiar_codigo(self, codigo: str) -> CredencialesDelegadasGraph:
        """Valida el código y devuelve el usuario propietario del token."""


class RenovadorTokenOAuth(Protocol):
    """Renueva un refresh token delegado sin exponerlo fuera del proceso."""

    async def renovar_refresh_token(self, refresh_token: str) -> TokensRenovadosGraph:
        """Devuelve un access token corto y el refresh token actualizado."""
