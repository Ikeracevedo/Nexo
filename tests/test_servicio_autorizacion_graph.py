"""El flujo OAuth une una respuesta de Entra con el usuario que la pidió."""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

import pytest

from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.puertos.oauth_graph import CredencialesDelegadasGraph
from app.servicios.servicio_autorizacion_graph import ServicioAutorizacionGraph

USUARIO = "usuario-aad"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _EstadosFalsos:
    def __init__(self, usuario: str | None = USUARIO) -> None:
        self.usuario = usuario
        self.creados: list[tuple[str, str, datetime]] = []

    async def crear(self, estado: str, usuario_id: str, expira_en: datetime) -> None:
        self.creados.append((estado, usuario_id, expira_en))

    async def consumir(self, estado: str, ahora: datetime) -> str | None:
        return self.usuario


class _IntercambiadorFalso:
    def __init__(self, usuario: str = USUARIO) -> None:
        self.usuario = usuario

    async def intercambiar_codigo(self, codigo: str) -> CredencialesDelegadasGraph:
        return CredencialesDelegadasGraph(self.usuario, "refresh-token")


class _CredencialesFalsas:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, str, datetime]] = []

    async def guardar_refresh_token(self, usuario: str, token: str, ahora: datetime) -> None:
        self.guardados.append((usuario, token, ahora))

    async def obtener_refresh_token(self, usuario: str) -> str | None:
        return None

    async def borrar_credenciales(self, usuario: str) -> None:
        pass


class _PreferenciasFalsas:
    def __init__(self) -> None:
        self.activadas: list[tuple[str, datetime]] = []

    async def activar_vigilancia(self, usuario: str, ahora: datetime) -> None:
        self.activadas.append((usuario, ahora))

    async def vigilancia_activa(self, usuario: str) -> bool:
        return False

    async def desactivar_vigilancia(self, usuario: str) -> None:
        pass


def _servicio(
    usuario_intercambiado: str = USUARIO,
) -> tuple[
    ServicioAutorizacionGraph,
    _EstadosFalsos,
    _CredencialesFalsas,
    _PreferenciasFalsas,
]:
    config = Configuracion(
        azure_tenant_id="00000000-0000-0000-0000-000000000001",
        azure_client_id="00000000-0000-0000-0000-000000000002",
        azure_redirect_uri="https://brujula-teams.duckdns.org/auth/callback",
    )
    estados = _EstadosFalsos()
    credenciales = _CredencialesFalsas()
    preferencias = _PreferenciasFalsas()
    return (
        ServicioAutorizacionGraph(
            config,
            estados,
            _IntercambiadorFalso(usuario_intercambiado),
            credenciales,
            preferencias,
        ),
        estados,
        credenciales,
        preferencias,
    )


async def test_crear_enlace_usa_estado_opaco_y_scopes_delegados() -> None:
    servicio, estados, _, _ = _servicio()

    enlace = await servicio.crear_enlace(USUARIO, AHORA)

    parametros = parse_qs(urlparse(enlace).query)
    estado = parametros["state"][0]
    assert parametros["redirect_uri"] == ["https://brujula-teams.duckdns.org/auth/callback"]
    assert "offline_access" in parametros["scope"][0]
    assert estados.creados[0][0] == estado
    assert estados.creados[0][1] == USUARIO
    assert USUARIO not in enlace


async def test_completar_guarda_token_y_activa_vigilancia() -> None:
    servicio, _, credenciales, preferencias = _servicio()

    await servicio.completar("estado", "codigo", AHORA)

    assert credenciales.guardados == [(USUARIO, "refresh-token", AHORA)]
    assert preferencias.activadas == [(USUARIO, AHORA)]


async def test_completar_rechaza_cuenta_distinta_a_la_que_inicio_el_flujo() -> None:
    servicio, _, credenciales, preferencias = _servicio("otro-usuario")

    with pytest.raises(FuenteNoDisponibleError, match="no coincide"):
        await servicio.completar("estado", "codigo", AHORA)

    assert not credenciales.guardados
    assert not preferencias.activadas
