"""ServicioPendientesPropios: parseo determinista de fechas y escritura.

El parsing de fechas es logica de negocio no trivial: se testea exhaustivamente.
Sin LLM: 4 patrones fijos (hoy, manana, dia de semana, DD/MM). Si un
test falla, es un bug en el parseo, no en la red ni en el modelo.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from app.dominio.pendiente import FuentePendiente, Pendiente
from app.servicios.servicio_pendientes_propios import (
    ServicioPendientesPropios,
    _extraer_titulo_y_fecha,
)

# Martes 29 de septiembre de 2026
HOY = date(2026, 9, 29)
AHORA = datetime(2026, 9, 29, 10, 0, tzinfo=UTC)
UID = "aad-iker-00000000-0000-0000-0000-000000000001"


# ---------------------------------------------------------------------------
# Parseo de fechas: _extraer_titulo_y_fecha
# ---------------------------------------------------------------------------


def test_sin_indicador_devuelve_titulo_y_sin_fecha() -> None:
    titulo, fecha = _extraer_titulo_y_fecha("entregar el informe", HOY)
    assert titulo == "entregar el informe"
    assert fecha is None


def test_hoy_se_resuelve_como_fecha_actual() -> None:
    titulo, fecha = _extraer_titulo_y_fecha("comprar leche hoy", HOY)
    assert titulo == "comprar leche"
    assert fecha == HOY


def test_manana_se_resuelve_como_dia_siguiente() -> None:
    titulo, fecha = _extraer_titulo_y_fecha("revisar PR mañana", HOY)
    assert titulo == "revisar PR"
    assert fecha == HOY + timedelta(days=1)


def test_viernes_se_resuelve_como_proximo_viernes() -> None:
    # HOY es martes (weekday=1). Viernes = weekday 4. Faltan 3 dias.
    titulo, fecha = _extraer_titulo_y_fecha("entregar el informe el viernes", HOY)
    assert titulo == "entregar el informe"
    assert fecha is not None
    assert fecha.weekday() == 4  # viernes


def test_lunes_cuando_hoy_es_martes_va_a_la_semana_siguiente() -> None:
    # HOY es martes. Pedir el lunes va al proximo lunes (6 dias despues).
    _, fecha = _extraer_titulo_y_fecha("reunión el lunes", HOY)
    assert fecha is not None
    assert fecha.weekday() == 0  # lunes
    assert fecha > HOY


def test_mismo_dia_de_semana_va_a_la_semana_siguiente() -> None:
    # HOY es martes. Pedir el martes va al siguiente martes, no hoy.
    _, fecha = _extraer_titulo_y_fecha("hacer backup el martes", HOY)
    assert fecha is not None
    assert fecha > HOY


def test_fecha_numerica_sin_anio() -> None:
    _, fecha = _extraer_titulo_y_fecha("entregar el 5/10", HOY)
    assert fecha == date(2026, 10, 5)


def test_fecha_numerica_con_anio() -> None:
    _, fecha = _extraer_titulo_y_fecha("renovar contrato el 01/03/2027", HOY)
    assert fecha == date(2027, 3, 1)


def test_fecha_numerica_anio_corto() -> None:
    _, fecha = _extraer_titulo_y_fecha("algo el 10/01/27", HOY)
    assert fecha == date(2027, 1, 10)


def test_fecha_invalida_se_ignora_y_devuelve_sin_fecha() -> None:
    # 31/02 no existe; se trata como "sin fecha" en vez de romper
    titulo, fecha = _extraer_titulo_y_fecha("algo el 31/02", HOY)
    assert fecha is None
    # El titulo puede quedar con el artefacto de la fecha mal formada,
    # lo importante es que no explote
    assert isinstance(titulo, str)


def test_el_informe_no_confunde_el_como_indicador_de_dia() -> None:
    # "entregar el informe el viernes" -> titulo sin "el viernes"
    titulo, fecha = _extraer_titulo_y_fecha("entregar el informe el viernes", HOY)
    assert "informe" in titulo
    assert "viernes" not in titulo
    assert fecha is not None and fecha.weekday() == 4


def test_titulo_vacio_despues_de_extraer_fecha() -> None:
    # "el viernes" sin titulo -> titulo vacio
    titulo, fecha = _extraer_titulo_y_fecha("el viernes", HOY)
    assert titulo == ""
    assert fecha is not None


# ---------------------------------------------------------------------------
# ServicioPendientesPropios.recordar
# ---------------------------------------------------------------------------


class _RepositorioFalso:
    """Doble de PendientesRepository."""

    def __init__(self) -> None:
        self.llamadas: list[tuple[str, str, Any]] = []
        self.llamadas_completar: list[tuple[str, str]] = []
        self.llamadas_borrar: list[tuple[str, str]] = []

    async def guardar(self, usuario_id: str, titulo: str, vence: Any) -> Pendiente:
        self.llamadas.append((usuario_id, titulo, vence))
        return Pendiente(
            id="propio-test",
            titulo=titulo,
            fuente=FuentePendiente.PROPIO,
            url_origen="https://teams.microsoft.com",
            vence=vence,
            confianza=1.0,
        )

    async def completar(self, pendiente_id: str, usuario_id: str) -> bool:
        self.llamadas_completar.append((pendiente_id, usuario_id))
        return True

    async def borrar(self, pendiente_id: str, usuario_id: str) -> bool:
        self.llamadas_borrar.append((pendiente_id, usuario_id))
        return True


async def test_recordar_extrae_titulo_y_guarda() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)
    p = await svc.recordar("recuerdame comprar leche", UID, AHORA)
    assert p.titulo == "comprar leche"
    assert repo.llamadas[0][0] == UID


async def test_recordar_con_fecha_pasa_vence_al_repositorio() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)
    await svc.recordar("recuerdame entregar el informe el viernes", UID, AHORA)
    _, _, vence = repo.llamadas[0]
    assert vence is not None
    assert vence.weekday() == 4  # viernes


async def test_recordar_sin_fecha_pasa_vence_none() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)
    await svc.recordar("recuerdame revisar el código", UID, AHORA)
    _, _, vence = repo.llamadas[0]
    assert vence is None


async def test_recordar_sin_titulo_lanza_value_error() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)
    with pytest.raises(ValueError, match="titulo"):
        await svc.recordar("recuerdame", UID, AHORA)


async def test_recordar_acepta_acento_en_recuerdame() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)
    p = await svc.recordar("recuérdame comprar pan", UID, AHORA)
    assert p.titulo == "comprar pan"


async def test_completar_delega_en_el_repositorio_con_el_usuario() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)

    completado = await svc.completar("propio-abc", UID)

    assert completado is True
    assert repo.llamadas_completar == [("propio-abc", UID)]


async def test_borrar_delega_en_el_repositorio_con_el_usuario() -> None:
    repo = _RepositorioFalso()
    svc = ServicioPendientesPropios(repo)

    borrado = await svc.borrar("propio-abc", UID)

    assert borrado is True
    assert repo.llamadas_borrar == [("propio-abc", UID)]
