"""El canal de Teams se prueba sin Teams.

Lo unico que NO se puede cubrir aqui son las tres lineas de los handlers
que hacen entrada/salida contra el SDK. Esa es exactamente la superficie
que la Capa de Bot Delgada (ADR-001) busca minimizar: si esta suite
cubre casi todo el canal, la capa es delgada de verdad.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import FastAPI
from microsoft_teams.api import MessageActivity
from microsoft_teams.api.models.account import Account, ConversationAccount

from app.bot.bot_teams import (
    PATRON_AGENDA,
    PATRON_AYUDA,
    PATRON_CHAT,
    PATRON_NO_VIGILAR,
    PATRON_RECUERDAME,
    PATRON_REVISAR,
    PATRON_VIGILAR,
    _usuario_id,
    construir_respuesta_agenda,
    construir_respuesta_revision,
    crear_bot_teams,
    procesar_accion_pendiente,
    procesar_accion_sugerencia,
    texto_ayuda,
)
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.dominio.pendiente import FuentePendiente, Pendiente
from app.dominio.sugerencia import DeQuien, Sugerencia
from app.puertos.fuente_mensajes import MensajeConversacion
from app.servicios.servicio_agenda import ServicioAgenda
from app.servicios.servicio_pendientes_propios import ServicioPendientesPropios

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


class _RepositorioAccionesFalso:
    def __init__(self, encontrado: bool = True) -> None:
        self.encontrado = encontrado
        self.completados: list[tuple[str, str]] = []
        self.borrados: list[tuple[str, str]] = []

    async def guardar(
        self,
        usuario_id: str,
        titulo: str,
        vence: datetime | None,
    ) -> Pendiente:
        return Pendiente(
            id="propio-test",
            titulo=titulo,
            fuente=FuentePendiente.PROPIO,
            url_origen="https://teams.microsoft.com",
            vence=vence,
        )

    async def completar(self, pendiente_id: str, usuario_id: str) -> bool:
        self.completados.append((pendiente_id, usuario_id))
        return self.encontrado

    async def borrar(self, pendiente_id: str, usuario_id: str) -> bool:
        self.borrados.append((pendiente_id, usuario_id))
        return self.encontrado


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


def test_reconoce_comandos_de_vigilancia() -> None:
    for frase in ["vigilar", " VIGILAR "]:
        assert PATRON_VIGILAR.match(frase), f"No reconocio: {frase!r}"
    for frase in ["no vigilar", "NO VIGILAR"]:
        assert PATRON_NO_VIGILAR.match(frase), f"No reconocio: {frase!r}"


def test_ayuda_explica_como_activar_y_apagar_vigilancia() -> None:
    ayuda = texto_ayuda("Nexo")

    assert "`vigilar`" in ayuda
    assert "`no vigilar`" in ayuda


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


async def test_completar_desde_tarjeta_delega_y_confirma() -> None:
    repo = _RepositorioAccionesFalso()
    servicio = ServicioPendientesPropios(repo)

    respuesta = await procesar_accion_pendiente(
        servicio,
        "completar_pendiente",
        "propio-abc",
        "usuario-a",
    )

    assert repo.completados == [("propio-abc", "usuario-a")]
    assert respuesta == "✅ Pendiente marcado como listo."


async def test_borrar_desde_tarjeta_delega_y_confirma() -> None:
    repo = _RepositorioAccionesFalso()
    servicio = ServicioPendientesPropios(repo)

    respuesta = await procesar_accion_pendiente(
        servicio,
        "borrar_pendiente",
        "propio-abc",
        "usuario-a",
    )

    assert repo.borrados == [("propio-abc", "usuario-a")]
    assert respuesta == "🗑️ Pendiente borrado."


async def test_accion_desconocida_no_modifica_pendientes() -> None:
    repo = _RepositorioAccionesFalso()
    servicio = ServicioPendientesPropios(repo)

    respuesta = await procesar_accion_pendiente(
        servicio,
        "otra_accion",
        "propio-abc",
        "usuario-a",
    )

    assert repo.completados == []
    assert repo.borrados == []
    assert respuesta == "No entendí la acción solicitada."


async def test_pendiente_ausente_no_revela_si_pertenece_a_otra_persona() -> None:
    repo = _RepositorioAccionesFalso(encontrado=False)
    servicio = ServicioPendientesPropios(repo)

    respuesta = await procesar_accion_pendiente(
        servicio,
        "completar_pendiente",
        "propio-abc",
        "usuario-a",
    )

    assert respuesta == "No encontré ese pendiente. Puede que ya haya cambiado."


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


# --- Identidad del usuario ----------------------------------------------


def _ctx_con_remitente(remitente: Account) -> Any:
    """Un ctx minimo con una actividad REAL del SDK: si el SDK renombra el
    campo, este test falla aqui y no en produccion (donde costo un 500)."""
    actividad = MessageActivity(
        from_=remitente,
        conversation=ConversationAccount(id="c1", conversation_type="personal"),
        id="1",
        recipient=Account(id="bot"),
        text="hola",
    )
    return SimpleNamespace(activity=actividad)


def test_el_usuario_se_identifica_por_su_aad_object_id() -> None:
    ctx = _ctx_con_remitente(
        Account(id="29:abc", aad_object_id="11111111-2222-3333-4444-555555555555")
    )
    assert _usuario_id(ctx) == "11111111-2222-3333-4444-555555555555"


def test_sin_aad_object_id_se_usa_el_id_del_canal() -> None:
    assert _usuario_id(_ctx_con_remitente(Account(id="29:abc"))) == "29:abc"


class _FuenteMensajesFalsa:
    def __init__(self, mensajes: list[MensajeConversacion]) -> None:
        self.mensajes = mensajes
        self.ultima_consulta: tuple[datetime, int] | None = None

    async def mensajes_recientes(self, desde: datetime, tope: int) -> list[MensajeConversacion]:
        self.ultima_consulta = (desde, tope)
        return self.mensajes


class _DetectorFalso:
    def __init__(self, sugerencias: list[Sugerencia]) -> None:
        self.sugerencias = sugerencias

    async def detectar(
        self, mensajes: list[MensajeConversacion], ahora: datetime
    ) -> list[Sugerencia]:
        return self.sugerencias


class _ServicioSugerenciasFalso:
    def __init__(self, sugerencias: list[Sugerencia], pendiente: Pendiente | None = None) -> None:
        self.sugerencias = sugerencias
        self.pendiente = pendiente
        self.guardadas: tuple[str, list[Sugerencia], datetime] | None = None
        self.descartadas: list[tuple[str, str]] = []

    async def guardar_detectadas(
        self, usuario_id: str, sugerencias: list[Sugerencia], detectadas_en: datetime
    ) -> None:
        self.guardadas = (usuario_id, sugerencias, detectadas_en)

    async def pendientes(self, usuario_id: str) -> list[Sugerencia]:
        return self.sugerencias

    async def aceptar(self, sugerencia_id: str, usuario_id: str) -> Pendiente | None:
        return self.pendiente

    async def descartar(self, sugerencia_id: str, usuario_id: str) -> bool:
        self.descartadas.append((sugerencia_id, usuario_id))
        return True


def _sugerencia_para_bot() -> Sugerencia:
    return Sugerencia(
        id="507f1f77bcf86cd799439011",
        texto="Enviar el informe",
        confianza=0.9,
        id_mensaje="mensaje-1",
        url_mensaje="https://teams.microsoft.com/l/message/chat/mensaje-1",
        conversacion="Proyecto TIC",
        de_quien=DeQuien.USUARIO,
    )


def test_reconoce_el_comando_revisar() -> None:
    assert PATRON_REVISAR.match("revisar")
    assert PATRON_REVISAR.match(" REVISAR ")


async def test_revisar_usa_ventana_corta_y_muestra_la_bandeja() -> None:
    mensaje = MensajeConversacion(
        id="mensaje-1",
        texto="Manana envio el informe.",
        autor="Iker",
        es_del_usuario=True,
        enviado_en=AHORA,
        conversacion="Proyecto TIC",
        url="https://teams.microsoft.com/l/message/chat/mensaje-1",
    )
    sugerencia = _sugerencia_para_bot()
    fuente = _FuenteMensajesFalsa([mensaje])
    servicio = _ServicioSugerenciasFalso([sugerencia])

    respuesta = await construir_respuesta_revision(
        cast(Any, fuente),
        cast(Any, _DetectorFalso([sugerencia])),
        cast(Any, servicio),
        "usuario-a",
        AHORA,
        "Nexo",
    )

    assert fuente.ultima_consulta == (AHORA - timedelta(days=7), 300)
    assert servicio.guardadas == ("usuario-a", [sugerencia], AHORA)
    assert "Posibles pendientes" in str(respuesta.model_dump(exclude_none=True))


async def test_las_acciones_de_sugerencia_aceptan_y_descartan() -> None:
    pendiente = Pendiente(
        id="propio-1",
        titulo="Enviar el informe",
        fuente=FuentePendiente.PROPIO,
        url_origen="https://teams.microsoft.com",
    )
    servicio = _ServicioSugerenciasFalso([], pendiente)

    aceptada = await procesar_accion_sugerencia(
        cast(Any, servicio), "aceptar_sugerencia", "sugerencia-1", "usuario-a"
    )
    descartada = await procesar_accion_sugerencia(
        cast(Any, servicio), "descartar_sugerencia", "sugerencia-1", "usuario-a"
    )

    assert "Enviar el informe" in aceptada
    assert servicio.descartadas == [("sugerencia-1", "usuario-a")]
    assert "No volver" in descartada
