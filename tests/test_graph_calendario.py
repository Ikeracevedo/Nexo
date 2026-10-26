"""El adaptador de Graph se prueba sin Graph, sin red y sin tenant.

Se le pasa un cliente falso con la misma FORMA que el real. Esa es la
ventaja de haber recibido el cliente por constructor en vez de crearlo
dentro: el adaptador no sabe si le dieron el de Microsoft o uno de
mentira.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.adaptadores.graph_calendario import URL_CALENDARIO, FuenteCalendarioGraph
from app.dominio.errores import FuenteNoDisponibleError, FuenteSinPermisoError
from app.dominio.pendiente import FuentePendiente

AHORA = datetime(2026, 9, 13, 10, 0, tzinfo=UTC)
LUEGO = AHORA + timedelta(days=7)


class _Fecha:
    def __init__(self, date_time: str | None, time_zone: str = "UTC") -> None:
        self.date_time = date_time
        self.time_zone = time_zone


class _Evento:
    def __init__(
        self,
        id: str = "e1",
        subject: str = "Clase",
        inicio: str | None = None,
        web_link: str | None = "https://outlook.office.com/x",
    ) -> None:
        self.id = id
        self.subject = subject
        self.start = _Fecha(inicio or "2026-09-15T14:00:00.0000000")
        self.web_link = web_link


class _Respuesta:
    def __init__(self, value: list[Any]) -> None:
        self.value = value


class _GraphFalso:
    """Misma forma que msgraph: cliente.me.calendar_view.get(...)"""

    def __init__(self, eventos: list[Any] | None = None, error: Exception | None = None) -> None:
        self._eventos = eventos or []
        self._error = error
        self.me = self
        self.calendar_view = self

    async def get(self, request_configuration: Any = None) -> Any:
        self.ultima_config = request_configuration
        if self._error:
            raise self._error
        return _Respuesta(self._eventos)


class _ErrorGraph(Exception):
    def __init__(self, codigo: int) -> None:
        self.response_status_code = codigo
        super().__init__(f"Graph {codigo}")


# --- Camino feliz -----------------------------------------------------


async def test_traduce_un_evento_a_pendiente() -> None:
    fuente = FuenteCalendarioGraph(_GraphFalso([_Evento(subject="Sustentacion")]))
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert p.titulo == "Sustentacion"
    assert p.fuente is FuentePendiente.CALENDARIO
    assert p.confianza == 1.0
    assert p.es_inferido is False


async def test_pide_la_ventana_correcta_a_graph() -> None:
    g = _GraphFalso([])
    await FuenteCalendarioGraph(g).obtener_pendientes(AHORA, LUEGO)

    # Extraer las propiedades del objeto RequestConfiguration y luego query_parameters
    query_params = g.ultima_config.query_parameters
    assert query_params.start_date_time == AHORA.isoformat()
    assert query_params.end_date_time == LUEGO.isoformat()
    assert g.ultima_config.headers["Prefer"] == 'outlook.timezone="UTC"'


async def test_sin_eventos_devuelve_lista_vacia_no_error() -> None:
    assert await FuenteCalendarioGraph(_GraphFalso([])).obtener_pendientes(AHORA, LUEGO) == []


# --- La regla no negociable: fallo != vacio ---------------------------


async def test_un_403_es_falta_de_permiso_no_una_agenda_vacia() -> None:
    fuente = FuenteCalendarioGraph(_GraphFalso(error=_ErrorGraph(403)))
    with pytest.raises(FuenteSinPermisoError) as e:
        await fuente.obtener_pendientes(AHORA, LUEGO)
    assert e.value.permiso_requerido == "Calendars.Read"
    assert e.value.nombre_fuente == "calendario"


async def test_un_401_tambien_es_falta_de_permiso() -> None:
    with pytest.raises(FuenteSinPermisoError):
        fuente = FuenteCalendarioGraph(_GraphFalso(error=_ErrorGraph(401)))
        await fuente.obtener_pendientes(AHORA, LUEGO)


async def test_un_500_es_fuente_caida_pero_NO_sin_permiso() -> None:
    """Distinguir importa: un 403 se arregla iniciando sesion; un 500, no.
    Ofrecerle 'conectar tu cuenta' a alguien cuyo problema es un 500 es
    mandarlo a dar vueltas."""
    with pytest.raises(FuenteNoDisponibleError) as e:
        fuente = FuenteCalendarioGraph(_GraphFalso(error=_ErrorGraph(500)))
        await fuente.obtener_pendientes(AHORA, LUEGO)
    assert not isinstance(e.value, FuenteSinPermisoError)


async def test_un_error_de_red_sin_codigo_tambien_se_reporta() -> None:
    with pytest.raises(FuenteNoDisponibleError):
        fuente = FuenteCalendarioGraph(_GraphFalso(error=TimeoutError("sin red")))
        await fuente.obtener_pendientes(AHORA, LUEGO)


# --- Casos borde ------------------------------------------------------


async def test_un_evento_sin_enlace_usa_el_calendario_como_origen() -> None:
    """Trazabilidad menos precisa, pero verdadera. Descartar el evento
    en silencio seria peor: perder pendientes sin avisar."""
    fuente = FuenteCalendarioGraph(_GraphFalso([_Evento(web_link=None)]))
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert p.url_origen == URL_CALENDARIO


async def test_un_evento_sin_titulo_se_descarta_sin_romper_la_agenda() -> None:
    eventos = [_Evento(id="ok", subject="Valido"), _Evento(id="malo", subject="   ")]
    ps = await FuenteCalendarioGraph(_GraphFalso(eventos)).obtener_pendientes(AHORA, LUEGO)
    assert [p.titulo for p in ps] == ["Valido"]


async def test_una_fecha_ilegible_no_tumba_el_evento() -> None:
    fuente = FuenteCalendarioGraph(_GraphFalso([_Evento(inicio="no-es-fecha")]))
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert p.vence is None


async def test_normaliza_a_utc_la_fecha_de_calendario_sin_zona_horaria() -> None:
    [pendiente] = await FuenteCalendarioGraph(_GraphFalso([_Evento()])).obtener_pendientes(
        AHORA, LUEGO
    )
    assert pendiente.vence is not None
    assert pendiente.vence.tzinfo is UTC
