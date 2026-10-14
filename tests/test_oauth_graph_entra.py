"""El adaptador OAuth no acepta tokens cuyo propietario no pueda verificarse."""

from __future__ import annotations

import httpx

from app.adaptadores.oauth_graph_entra import IntercambiadorCodigoEntra
from app.config import Configuracion


def _config() -> Configuracion:
    return Configuracion(
        azure_tenant_id="00000000-0000-0000-0000-000000000001",
        azure_client_id="00000000-0000-0000-0000-000000000002",
        azure_client_secret="secreto",
        azure_redirect_uri="https://brujula-teams.duckdns.org/auth/callback",
    )


async def test_intercambiar_codigo_verifica_perfil_y_devuelve_solo_refresh_token() -> None:
    peticiones: list[httpx.Request] = []

    def responder(solicitud: httpx.Request) -> httpx.Response:
        peticiones.append(solicitud)
        if solicitud.url.host == "login.microsoftonline.com":
            return httpx.Response(200, json={"access_token": "access", "refresh_token": "refresh"})
        return httpx.Response(200, json={"id": "usuario-aad"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(responder)) as cliente:
        intercambiador = IntercambiadorCodigoEntra(_config(), _cliente=cliente)
        resultado = await intercambiador.intercambiar_codigo("codigo")

    assert resultado.usuario_id == "usuario-aad"
    assert resultado.refresh_token == "refresh"
    assert peticiones[1].headers["authorization"] == "Bearer access"


async def test_renovar_refresh_token_conserva_la_rotacion_de_entra() -> None:
    def responder(solicitud: httpx.Request) -> httpx.Response:
        assert solicitud.url.host == "login.microsoftonline.com"
        return httpx.Response(
            200,
            json={"access_token": "access-nuevo", "refresh_token": "refresh-nuevo"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(responder)) as cliente:
        intercambiador = IntercambiadorCodigoEntra(_config(), _cliente=cliente)
        resultado = await intercambiador.renovar_refresh_token("refresh-anterior")

    assert resultado.access_token == "access-nuevo"
    assert resultado.refresh_token == "refresh-nuevo"
