"""La precarga respeta consentimiento, intervalo y cambios de mensajes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.dominio.precarga import EstadoPrecarga
from app.puertos.fuente_mensajes import MensajeConversacion
from app.puertos.oauth_graph import TokensRenovadosGraph
from app.servicios.servicio_precarga import ServicioPrecarga

USUARIO = "usuario-aad"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _PreferenciasFalsas:
    async def usuarios_con_vigilancia_activa(self) -> list[str]:
        return [USUARIO]

    async def vigilancia_activa(self, usuario_id: str) -> bool:
        return usuario_id == USUARIO

    async def activar_vigilancia(self, usuario_id: str, activada_en: datetime) -> None:
        pass

    async def desactivar_vigilancia(self, usuario_id: str) -> None:
        pass


class _CredencialesFalsas:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, str, datetime]] = []

    async def obtener_refresh_token(self, usuario_id: str) -> str | None:
        return "refresh-anterior"

    async def guardar_refresh_token(self, usuario_id: str, token: str, ahora: datetime) -> None:
        self.guardados.append((usuario_id, token, ahora))

    async def borrar_credenciales(self, usuario_id: str) -> None:
        pass


class _RenovadorFalso:
    async def renovar_refresh_token(self, refresh_token: str) -> TokensRenovadosGraph:
        return TokensRenovadosGraph("access", "refresh-nuevo")


class _FuenteFalsa:
    async def mensajes_recientes(self, desde: datetime, tope: int) -> list[MensajeConversacion]:
        return [
            MensajeConversacion(
                id="m-1",
                texto="contenido que no debe entrar a la huella",
                autor="Iker",
                es_del_usuario=True,
                enviado_en=AHORA,
                conversacion="Chat",
                url="https://teams.microsoft.com/m-1",
            )
        ]


class _FabricaFalsa:
    def crear(self, usuario_id: str, access_token: str) -> _FuenteFalsa:
        return _FuenteFalsa()


class _DetectorFalso:
    def __init__(self) -> None:
        self.llamadas = 0

    async def detectar(self, mensajes: list[MensajeConversacion], ahora: datetime) -> list[Any]:
        self.llamadas += 1
        return []


class _SugerenciasFalsas:
    def __init__(self) -> None:
        self.guardadas = 0

    async def guardar_nuevas(
        self, usuario_id: str, sugerencias: list[Any], ahora: datetime
    ) -> None:
        self.guardadas += 1


class _EstadoFalso:
    def __init__(self, estado: EstadoPrecarga | None = None) -> None:
        self.estado = estado

    async def obtener(self, usuario_id: str) -> EstadoPrecarga | None:
        return self.estado

    async def guardar(self, usuario_id: str, estado: EstadoPrecarga) -> None:
        self.estado = estado


def _servicio(
    estado: EstadoPrecarga | None = None,
) -> tuple[ServicioPrecarga, _DetectorFalso, _SugerenciasFalsas]:
    detector = _DetectorFalso()
    sugerencias = _SugerenciasFalsas()
    servicio = ServicioPrecarga(
        cast(Any, _PreferenciasFalsas()),
        _CredencialesFalsas(),
        _RenovadorFalso(),
        cast(Any, _FabricaFalsa()),
        cast(Any, detector),
        cast(Any, sugerencias),
        _EstadoFalso(estado),
    )
    return servicio, detector, sugerencias


async def test_precarga_detecta_y_guarda_cuando_no_hay_estado_previo() -> None:
    servicio, detector, sugerencias = _servicio()

    actualizados = await servicio.actualizar_todos(AHORA)

    assert actualizados == 1
    assert detector.llamadas == 1
    assert sugerencias.guardadas == 1


async def test_precarga_no_lee_ni_renueva_antes_del_intervalo() -> None:
    servicio, detector, sugerencias = _servicio(
        EstadoPrecarga(AHORA - timedelta(minutes=10), "huella")
    )

    actualizados = await servicio.actualizar_todos(AHORA)

    assert actualizados == 0
    assert detector.llamadas == 0
    assert sugerencias.guardadas == 0


async def test_precarga_omite_el_modelo_si_la_huella_no_cambio() -> None:
    servicio, detector, sugerencias = _servicio()
    huella = servicio._huella(await _FuenteFalsa().mensajes_recientes(AHORA, 300))
    servicio, detector, sugerencias = _servicio(EstadoPrecarga(AHORA - timedelta(hours=1), huella))

    actualizados = await servicio.actualizar_todos(AHORA)

    assert actualizados == 0
    assert detector.llamadas == 0
    assert sugerencias.guardadas == 0
