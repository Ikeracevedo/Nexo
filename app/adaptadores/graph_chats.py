"""Adaptador Graph para leer mensajes recientes de chats.

Solo entrega mensajes normalizados en memoria. Nunca persiste cuerpos de Teams:
la detección y cualquier almacenamiento posterior pertenecen a otros casos de uso.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.chats.chats_request_builder import ChatsRequestBuilder
from msgraph.generated.chats.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)

from app.dominio.errores import FuenteNoDisponibleError, FuenteSinPermisoError
from app.puertos.fuente_mensajes import MensajeConversacion

logger = logging.getLogger(__name__)

NOMBRE = "chats"
PERMISO = "Chat.Read"
_MAXIMO_POR_CHAT = 50


class _ExtractorTextoHTML(HTMLParser):
    """Extrae texto visible y conserva separaciones semánticas de HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []

    def handle_data(self, data: str) -> None:
        self.partes.append(data)

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag in {"br", "p", "div", "li"}:
            self.partes.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li"}:
            self.partes.append(" ")

    def texto(self) -> str:
        return " ".join("".join(self.partes).split())


def _limpiar_html(html: str) -> str:
    """Convierte el cuerpo HTML de Graph a texto plano antes de analizarlo."""
    extractor = _ExtractorTextoHTML()
    extractor.feed(html)
    extractor.close()
    return extractor.texto()


class FuenteChatsGraph:
    """Lee mensajes recientes sin permitir que un chat roto bloquee los demás."""

    def __init__(
        self,
        cliente_graph: Any,
        usuario_id: str,
        bot_id: str,
    ) -> None:
        self._graph = cliente_graph
        self._usuario_id = usuario_id
        self._bot_id = bot_id

    @property
    def nombre(self) -> str:
        return NOMBRE

    async def mensajes_recientes(
        self,
        desde: datetime,
        tope: int,
    ) -> list[MensajeConversacion]:
        try:
            respuesta = await self._graph.me.chats.get(
                request_configuration=self._configuracion_chats()
            )
        except Exception as error:
            raise self._traducir_error(error) from error

        chats = getattr(respuesta, "value", None) or []
        resultados = await asyncio.gather(
            *(self._mensajes_de_chat(chat, desde) for chat in chats),
            return_exceptions=True,
        )

        mensajes: list[MensajeConversacion] = []
        for chat, resultado in zip(chats, resultados, strict=True):
            if isinstance(resultado, BaseException):
                logger.warning(
                    "No se pudieron leer mensajes del chat %s: %s",
                    getattr(chat, "id", "?"),
                    resultado,
                )
                continue
            mensajes.extend(resultado)

        mensajes.sort(key=lambda mensaje: mensaje.enviado_en, reverse=True)
        return mensajes[:tope]

    async def _mensajes_de_chat(
        self,
        chat: Any,
        desde: datetime,
    ) -> list[MensajeConversacion]:
        chat_id = getattr(chat, "id", None)
        if not chat_id:
            return []

        try:
            respuesta = await self._graph.chats.by_chat_id(chat_id).messages.get(
                request_configuration=self._configuracion_mensajes(desde)
            )
        except Exception as error:
            raise self._traducir_error(error) from error

        nombre_chat = (getattr(chat, "topic", None) or "Chat privado").strip()
        mensajes = getattr(respuesta, "value", None) or []

        return [
            mensaje_normalizado
            for mensaje in mensajes
            if (
                mensaje_normalizado := self._a_mensaje(
                    mensaje,
                    nombre_chat,
                )
            )
            is not None
        ]

    @staticmethod
    def _configuracion_chats() -> RequestConfiguration[Any]:
        parametros = ChatsRequestBuilder.ChatsRequestBuilderGetQueryParameters(
            orderby=["lastMessagePreview/createdDateTime desc"],
            top=_MAXIMO_POR_CHAT,
        )
        return RequestConfiguration(query_parameters=parametros)

    @staticmethod
    def _configuracion_mensajes(desde: datetime) -> RequestConfiguration[Any]:
        parametros = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            filter=f"lastModifiedDateTime gt {desde.isoformat()}",
            orderby=["lastModifiedDateTime desc"],
            top=_MAXIMO_POR_CHAT,
        )
        return RequestConfiguration(query_parameters=parametros)

    def _a_mensaje(
        self,
        mensaje: Any,
        nombre_chat: str,
    ) -> MensajeConversacion | None:
        tipo_mensaje = getattr(mensaje, "message_type", None)
        if getattr(tipo_mensaje, "value", tipo_mensaje) != "message":
            return None

        remitente = getattr(mensaje, "from_", None)
        usuario = getattr(remitente, "user", None)
        aplicacion = getattr(remitente, "application", None)

        remitente_id = getattr(usuario, "id", None)
        aplicacion_id = getattr(aplicacion, "id", None)
        if remitente_id == self._bot_id or aplicacion_id == self._bot_id:
            return None

        texto = _limpiar_html(getattr(getattr(mensaje, "body", None), "content", "") or "")
        mensaje_id = getattr(mensaje, "id", None)
        enviado_en = getattr(mensaje, "created_date_time", None)
        url = getattr(mensaje, "web_url", None)

        if not texto or not mensaje_id or not enviado_en or not url:
            return None

        return MensajeConversacion(
            id=mensaje_id,
            texto=texto,
            autor=(getattr(usuario, "display_name", None) or "Desconocido").strip(),
            es_del_usuario=remitente_id == self._usuario_id,
            enviado_en=enviado_en,
            conversacion=nombre_chat,
            url=url,
        )

    @staticmethod
    def _traducir_error(error: Exception) -> FuenteNoDisponibleError:
        codigo = getattr(error, "response_status_code", None)
        if codigo in (401, 403):
            return FuenteSinPermisoError(NOMBRE, PERMISO)
        return FuenteNoDisponibleError(
            NOMBRE,
            f"Graph respondio {codigo or type(error).__name__}",
        )
