"""El adaptador de chats se prueba sin Graph ni red."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from types import SimpleNamespace
from typing import Any

import pytest

from app.adaptadores.graph_chats import FuenteChatsGraph, _limpiar_html
from app.dominio.errores import FuenteSinPermisoError

AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _TipoMensaje(Enum):
    NORMAL = "message"
    SISTEMA = "systemEventMessage"


class _ErrorGraph(Exception):
    def __init__(self, codigo: int) -> None:
        self.response_status_code = codigo


class _SolicitudFalsa:
    def __init__(self, resultado: list[Any] | Exception) -> None:
        self._resultado = resultado
        self.configuraciones: list[Any] = []

    async def get(self, request_configuration: Any = None) -> Any:
        self.configuraciones.append(request_configuration)
        if isinstance(self._resultado, Exception):
            raise self._resultado
        return SimpleNamespace(value=self._resultado)


class _ChatsFalsos:
    def __init__(self, mensajes_por_chat: dict[str, list[Any] | Exception]) -> None:
        self._solicitudes = {
            chat_id: _SolicitudFalsa(mensajes) for chat_id, mensajes in mensajes_por_chat.items()
        }

    def by_chat_id(self, chat_id: str) -> Any:
        return SimpleNamespace(messages=self._solicitudes[chat_id])


class _GraphFalso:
    def __init__(
        self,
        chats: list[Any] | Exception,
        mensajes_por_chat: dict[str, list[Any] | Exception] | None = None,
    ) -> None:
        self.solicitud_chats = _SolicitudFalsa(chats)
        self.me = SimpleNamespace(chats=self.solicitud_chats)
        self.chats = _ChatsFalsos(mensajes_por_chat or {})


def _chat(chat_id: str, tema: str = "Proyecto TIC") -> Any:
    return SimpleNamespace(id=chat_id, topic=tema)


def _mensaje(
    mensaje_id: str,
    *,
    autor_id: str = "otro",
    autor: str = "Julian",
    texto: str = "<p>Enviar informe</p>",
    enviado_en: datetime = AHORA,
    tipo: str | _TipoMensaje = _TipoMensaje.NORMAL,
    url: str | None = None,
) -> Any:
    return SimpleNamespace(
        id=mensaje_id,
        message_type=tipo,
        from_=SimpleNamespace(
            user=SimpleNamespace(id=autor_id, display_name=autor),
            application=None,
        ),
        body=SimpleNamespace(content=texto),
        created_date_time=enviado_en,
        web_url=url or f"https://teams.microsoft.com/l/message/chat/{mensaje_id}",
    )


def test_limpia_etiquetas_html_antes_de_entregar_el_mensaje() -> None:
    texto = _limpiar_html("<p>Enviar <strong>el informe</strong><br>mañana</p>")

    assert texto == "Enviar el informe mañana"


def test_limpia_entidades_html_y_espacios_repetidos() -> None:
    texto = _limpiar_html("<div>Julian&nbsp;&amp;&nbsp;Iker</div>   <div>revisan</div>")

    assert texto == "Julian & Iker revisan"


@pytest.mark.asyncio
async def test_normaliza_mensajes_y_distingue_el_compromiso_del_usuario() -> None:
    chat = _chat("chat-1")
    graph = _GraphFalso(
        [chat],
        {
            "chat-1": [
                _mensaje("mio", autor_id="yo", autor="Iker", texto="<p>Yo envio<br>la info</p>"),
                _mensaje("otro", autor_id="julian"),
                _mensaje("sistema", tipo=_TipoMensaje.SISTEMA),
                _mensaje("bot", autor_id="bot"),
                _mensaje("vacio", texto="<p>   </p>"),
            ]
        },
    )

    mensajes = await FuenteChatsGraph(graph, usuario_id="yo", bot_id="bot").mensajes_recientes(
        AHORA - timedelta(days=7),
        tope=10,
    )

    assert [(mensaje.id, mensaje.es_del_usuario) for mensaje in mensajes] == [
        ("mio", True),
        ("otro", False),
    ]
    assert mensajes[0].texto == "Yo envio la info"
    assert mensajes[0].conversacion == "Proyecto TIC"


@pytest.mark.asyncio
async def test_consulta_la_ventana_con_el_orden_y_filtro_compatibles_con_graph() -> None:
    chat = _chat("chat-1")
    graph = _GraphFalso([chat], {"chat-1": []})
    desde = AHORA - timedelta(days=7)

    await FuenteChatsGraph(graph, usuario_id="yo", bot_id="bot").mensajes_recientes(desde, tope=10)

    parametros_chats = graph.solicitud_chats.configuraciones[0].query_parameters
    parametros_mensajes = graph.chats._solicitudes["chat-1"].configuraciones[0].query_parameters
    assert parametros_chats.orderby == ["lastMessagePreview/createdDateTime desc"]
    assert parametros_chats.top == 50
    assert parametros_mensajes.orderby == ["lastModifiedDateTime desc"]
    assert parametros_mensajes.filter == f"lastModifiedDateTime gt {desde.isoformat()}"
    assert parametros_mensajes.top == 50


@pytest.mark.asyncio
async def test_un_chat_que_falla_no_impide_devolver_los_demas() -> None:
    graph = _GraphFalso(
        [_chat("disponible"), _chat("roto")],
        {
            "disponible": [_mensaje("mensaje-disponible")],
            "roto": _ErrorGraph(500),
        },
    )

    mensajes = await FuenteChatsGraph(graph, usuario_id="yo", bot_id="bot").mensajes_recientes(
        AHORA - timedelta(days=7),
        tope=10,
    )

    assert [mensaje.id for mensaje in mensajes] == ["mensaje-disponible"]


@pytest.mark.asyncio
async def test_respeta_el_tope_global_y_devuelve_los_mas_recientes() -> None:
    graph = _GraphFalso(
        [_chat("uno"), _chat("dos")],
        {
            "uno": [
                _mensaje("viejo", enviado_en=AHORA - timedelta(hours=2)),
                _mensaje("reciente", enviado_en=AHORA),
            ],
            "dos": [_mensaje("medio", enviado_en=AHORA - timedelta(hours=1))],
        },
    )

    mensajes = await FuenteChatsGraph(graph, usuario_id="yo", bot_id="bot").mensajes_recientes(
        AHORA - timedelta(days=7),
        tope=2,
    )

    assert [mensaje.id for mensaje in mensajes] == ["reciente", "medio"]


@pytest.mark.asyncio
async def test_un_403_al_listar_chats_indica_que_falta_chat_read() -> None:
    fuente = FuenteChatsGraph(_GraphFalso(_ErrorGraph(403)), usuario_id="yo", bot_id="bot")

    with pytest.raises(FuenteSinPermisoError) as error:
        await fuente.mensajes_recientes(AHORA - timedelta(days=7), tope=10)

    assert error.value.nombre_fuente == "chats"
    assert error.value.permiso_requerido == "Chat.Read"
