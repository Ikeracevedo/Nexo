"""El canal de Teams se prueba sin Teams.

Lo unico que NO se puede cubrir aqui son las tres lineas de los handlers
que hacen entrada/salida contra el SDK. Esa es exactamente la superficie
que la Capa de Bot Delgada (ADR-001) busca minimizar: si esta suite
cubre casi todo el canal, la capa es delgada de verdad.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI

from app.bot.bot_teams import (
    PATRON_AGENDA,
    PATRON_AYUDA,
    PATRON_CHAT,
    PATRON_RECUERDAME,
    construir_respuesta_agenda,
    crear_bot_teams,
)
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.dominio.pendiente import FuentePendiente, Pendiente
from app.servicios.servicio_agenda import ServicioAgenda

AHORA = datetime(2026, 9, 8, 10, 0, 0)


class FuenteFalsa:
    def __init__(self, nombre: str, pendientes: list[Pendiente]) -> None:
        self._nombre = nombre
        self._pendientes = pendientes

    @property
    def nombre(self) -> str:
        return self._nombre

    async def obtener_pendientes(self, desde: datetime, hasta: datetime) -> list[Pendiente]:
        return self._pendientes


class FuenteRota:
    @property
    def nombre(self) -> str:
        return "planner"

    async def obtener_pendientes(self, desde: datetime, hasta: datetime) -> list[Pendiente]:
        raise FuenteNoDisponibleError("planner", "403 Forbidden")


def _p(id_: str, confianza: float = 1.0) -> Pendiente:
    return Pendiente(
        id=id_,
        titulo=f"Tarea {id_}",
        fuente=FuentePendiente.PLANNER,
        url_origen=f"https://teams.microsoft.com/l/entity/{id_}",
        vence=AHORA + timedelta(days=2),
        confianza=confianza,
    )


# --- Enrutamiento de intencion ----------------------------------------


def test_reconoce_las_formas_cortas_de_pedir_la_tarjeta() -> None:
    for frase in ["semana", "¿qué tengo?", "que tengo", "PENDIENTES", "mi agenda"]:
        assert PATRON_AGENDA.match(frase), f"No reconocio: {frase!r}"


def test_las_preguntas_naturales_van_a_la_ia_no_a_la_tarjeta() -> None:
    for frase in [
        "¿qué tengo para hacer hoy?",
        "qué hay para hoy",
        "¿tengo algo el viernes?",
        "¿qué tengo esta semana?",
    ]:
        assert not PATRON_AGENDA.match(frase), f"Deberia ir a la IA: {frase!r}"


def test_no_confunde_saludos_con_peticiones_de_agenda() -> None:
    for frase in ["hola", "ayuda", "?"]:
        assert PATRON_AYUDA.match(frase)
        assert not PATRON_AGENDA.search(frase)


def test_reconoce_recuerdame() -> None:
    for frase in ["recuérdame comprar leche", "recuerdame entregar el informe el viernes"]:
        assert PATRON_RECUERDAME.match(frase), f"No reconocio: {frase!r}"
    for frase in ["semana", "ayuda", "estado"]:
        assert not PATRON_RECUERDAME.match(frase)


def test_chat_no_se_confunde_con_pregunta_de_agenda() -> None:
    frase = "chat ¿qué tengo pendiente sobre este tema?"
    assert PATRON_CHAT.match(frase)
    assert not PATRON_AGENDA.search(frase)


def test_no_responde_fuera_de_alcance() -> None:
    """El plan: 'si preguntan por recetas de cocina, no responde'."""
    for frase in ["dame una receta de arepas", "quién ganó el mundial"]:
        assert not PATRON_AGENDA.search(frase)
        assert not PATRON_AYUDA.match(frase)


# --- La respuesta que se le manda a Teams -----------------------------


async def test_la_respuesta_lleva_una_tarjeta_adjunta() -> None:
    servicio = ServicioAgenda([FuenteFalsa("planner", [_p("a")])])
    mensaje = await construir_respuesta_agenda(servicio, AHORA)
    assert mensaje.attachments
    assert len(mensaje.attachments) == 1


async def test_la_tarjeta_refleja_los_pendientes_del_servicio() -> None:
    servicio = ServicioAgenda([FuenteFalsa("planner", [_p("a"), _p("b", confianza=0.6)])])
    mensaje = await construir_respuesta_agenda(servicio, AHORA)
    texto = str(mensaje.model_dump(exclude_none=True))
    assert "2 pendientes" in texto
    assert "60% — inferido" in texto


async def test_si_una_fuente_falla_la_tarjeta_lo_declara() -> None:
    """Recorrido completo del canal: servicio -> Agenda -> tarjeta.
    La regla no negociable de OT-01 llega intacta hasta la pantalla."""
    servicio = ServicioAgenda([FuenteFalsa("calendario", [_p("a")]), FuenteRota()])
    mensaje = await construir_respuesta_agenda(servicio, AHORA)
    texto = str(mensaje.model_dump(exclude_none=True))
    assert "No pude consultar" in texto
    assert "planner" in texto


async def test_sin_pendientes_y_sin_fallos_no_inventa_una_advertencia() -> None:
    servicio = ServicioAgenda([FuenteFalsa("planner", [])])
    mensaje = await construir_respuesta_agenda(servicio, AHORA)
    texto = str(mensaje.model_dump(exclude_none=True))
    assert "No tienes pendientes" in texto
    assert "No pude consultar" not in texto


GUID_BOT = "11111111-2222-3333-4444-555555555555"


def test_sin_bot_id_en_produccion_la_app_no_arranca() -> None:
    """Fallar cerrado: un secreto ausente no abre /api/messages, tumba el arranque."""
    config = Configuracion(brujula_entorno="produccion", teams_bot_id="")
    with pytest.raises(RuntimeError, match="TEAMS_BOT_ID"):
        crear_bot_teams(FastAPI(), config)


def test_sin_bot_id_en_local_si_arranca() -> None:
    """En local el modo sin autenticar es cómodo y está permitido."""
    config = Configuracion(brujula_entorno="local", teams_bot_id="")
    crear_bot_teams(FastAPI(), config)


def test_con_bot_id_en_produccion_si_arranca() -> None:
    config = Configuracion(brujula_entorno="produccion", teams_bot_id=GUID_BOT)
    crear_bot_teams(FastAPI(), config)
