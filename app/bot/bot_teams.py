"""Canal de Teams: adaptador PRIMARIO sobre el nucleo de Brujula.

CAPA DE BOT DELGADA — regla que no se negocia:
este modulo traduce mensajes de Teams a llamadas al servicio y respuestas
del servicio a tarjetas. NO decide nada del negocio.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime

from fastapi import FastAPI
from microsoft_teams.api import MessageActivity, MessageActivityInput, TypingActivityInput
from microsoft_teams.apps import ActivityContext, App
from microsoft_teams.apps.http.fastapi_adapter import FastAPIAdapter

from app.bot.descarga_adjuntos import descargar_adjuntos, tiene_adjuntos
from app.bot.tarjeta_agenda import tarjeta_agenda
from app.composicion import (
    servicio_chat_general,
    servicio_conversacion,
    servicio_para_usuario,
    servicio_pendientes_propios_para_usuario,
)
from app.config import Configuracion
from app.dominio.adjunto import Adjunto, AdjuntoNoSoportadoError
from app.dominio.conversacion import MemoriaNoDisponibleError
from app.servicios.servicio_agenda import ServicioAgenda
from app.servicios.servicio_chat_general import ServicioChatGeneral
from app.servicios.servicio_conversacion import ServicioConversacion

# Solo las formas CORTAS de pedir la tarjeta. Cualquier frase mas larga
# ("que tengo para hacer hoy") va a la IA, que razona sobre la agenda real.
PATRON_AGENDA = re.compile(
    r"^\s*¿?\s*(semana|mi\s+semana|pendientes|agenda|mi\s+agenda|qu[eé]\s+tengo)\s*\??\s*$",
    re.IGNORECASE,
)
PATRON_AYUDA = re.compile(r"^\s*(hola|ayuda|help|men[uú]|\?)\s*$", re.IGNORECASE)
PATRON_CONECTAR = re.compile(
    r"^\s*(conectar|conectarme|iniciar\s+sesi[oó]n|login)\s*$", re.IGNORECASE
)
PATRON_DESCONECTAR = re.compile(r"^\s*(desconectar|cerrar\s+sesi[oó]n|logout)\s*$", re.IGNORECASE)
PATRON_ESTADO = re.compile(r"^\s*(estado|status)\s*$", re.IGNORECASE)
PATRON_RECUERDAME = re.compile(r"^\s*rec[uú][eé]rdame\b", re.IGNORECASE)
PATRON_CHAT = re.compile(r"^\s*chat\b\s*", re.IGNORECASE)
PATRON_OLVIDAR = re.compile(r"^\s*olvidar\s*$", re.IGNORECASE)

AYUDA = (
    "**Brújula** — te ubica entre tus pendientes.\n\n"
    "- **`semana`** — qué tienes en los próximos 7 días\n"
    "- **`recuérdame <texto> [el viernes]`** — anota un pendiente propio\n"
    "- **`chat <pregunta>`** — conversación general con memoria; también puedes "
    "enviar imágenes, PDF, Word (.docx) y Excel (.xlsx)\n"
    "- **`olvidar`** — borra la memoria de tu conversación\n"
    "- **`conectar`** — autoriza a Brújula a leer tu calendario real\n"
    "- **`desconectar`** — revoca esa autorización\n"
    "- **`estado`** — si tus datos son reales o de ejemplo, ahora mismo\n"
    "- **`ayuda`** — este mensaje\n\n"
    "_También puedes preguntarme en lenguaje natural **sobre tus pendientes** "
    "(«¿qué es lo más urgente?», «¿tengo algo el viernes?»). "
    "Fuera de eso no respondo: no soy un asistente de propósito general._\n\n"
    "_Cada pendiente trae enlace a su origen. Los que Brújula infirió de una "
    "conversación salen marcados en amarillo con su nivel de confianza._"
)

NECESITO_PERMISO = (
    "Para mostrarte tus pendientes reales necesito tu autorización. "
    "Te va a aparecer un botón para iniciar sesión."
)


async def construir_respuesta_agenda(
    servicio: ServicioAgenda,
    ahora: datetime,
) -> MessageActivityInput:
    """Consulta la agenda y la convierte en el mensaje que ira a Teams.

    Vive FUERA del handler a proposito: todo lo que queda dentro de un
    handler del SDK solo se puede probar con Teams conectado; todo lo
    que sale de el se prueba con un pytest de 20 milisegundos.
    """
    agenda = await servicio.pendientes_de_la_semana(ahora)
    return MessageActivityInput().add_card(tarjeta_agenda(agenda, ahora))


async def construir_respuesta_libre(
    conversacion: ServicioConversacion,
    servicio: ServicioAgenda,
    pregunta: str,
    ahora: datetime,
) -> str:
    """Responde una pregunta libre ACOTADA a la agenda del usuario.

    Vive fuera del handler por el mismo motivo que `construir_respuesta_agenda`:
    lo que queda dentro de un handler solo se prueba con Teams conectado.
    """
    agenda = await servicio.pendientes_de_la_semana(ahora)
    respuesta = await conversacion.responder(pregunta, agenda, ahora)
    return respuesta.texto


async def construir_respuesta_chat(
    chat: ServicioChatGeneral,
    usuario_id: str,
    conversacion_id: str,
    mensaje: str,
    ahora: datetime,
    adjuntos: Sequence[Adjunto] = (),
) -> str:
    """Prueba el chat general sin depender del SDK ni de Teams conectado."""
    respuesta = await chat.responder(usuario_id, conversacion_id, mensaje, ahora, adjuntos)
    return respuesta.texto


def _usuario_id(ctx: ActivityContext) -> str:
    """AAD Object ID del usuario. Se prefiere sobre el ID de canal de Teams.

    aad_object_id es el GUID de Entra ID (el que se usa como clave en Mongo).
    Si no esta disponible se usa from_.id como fallback.

    El campo del SDK se llama `from_` (con guion bajo, porque `from` es palabra
    reservada de Python). Con `from_property` fallaba con AttributeError y
    rompia `chat`, `semana` y `recuerdame` en produccion.
    """
    remitente = ctx.activity.from_
    return (getattr(remitente, "aad_object_id", None) or getattr(remitente, "id", "") or "").strip()


def crear_bot_teams(
    nucleo: FastAPI,
    config: Configuracion,
) -> App:
    """Monta el canal de Teams sobre la app FastAPI del nucleo.

    Ya no recibe un ServicioAgenda del composition root: con datos reales,
    el servicio se construye POR PETICION, con el cliente de Graph del
    usuario que escribe. Un servicio pasado por fuera y compartido entre
    peticiones seria un servicio cacheado con el token de alguien -- la
    fuga de datos que se evito en F3.
    """

    es_local = config.brujula_entorno == "local"
    sin_credenciales = not config.teams_bot_id

    if sin_credenciales and not es_local:
        # Fallar CERRADO: un secreto ausente en produccion no se degrada a
        # "acepto cualquier peticion", se degrada a "no arranco".
        raise RuntimeError(
            "TEAMS_BOT_ID es obligatorio cuando BRUJULA_ENTORNO no es 'local'. "
            "Sin el, /api/messages aceptaria actividades no autenticadas."
        )

    bot = App(
        http_server_adapter=FastAPIAdapter(app=nucleo),
        messaging_endpoint="/api/messages",
        client_id=config.teams_bot_id or None,
        client_secret=config.teams_bot_password or None,
        tenant_id=config.azure_tenant_id or None,
        dangerously_allow_unauthenticated_requests=sin_credenciales and es_local,
        default_connection_name=config.teams_oauth_connection,
    )

    # El servicio de conversacion SI se puede construir una vez: no lleva
    # token de nadie. El de agenda NO, y por eso se crea por peticion.
    conversacion = servicio_conversacion(config)
    chat_general = servicio_chat_general(config)

    async def responder_chat(ctx: ActivityContext[MessageActivity]) -> None:
        """Convierte adjuntos de Teams y delega el contenido al caso de uso."""
        await ctx.reply(TypingActivityInput())
        try:
            adjuntos = await descargar_adjuntos(
                getattr(ctx.activity, "attachments", None) or [], config
            )
            pregunta = PATRON_CHAT.sub("", ctx.activity.text or "", count=1)
            texto = await construir_respuesta_chat(
                chat_general,
                _usuario_id(ctx),
                ctx.activity.conversation.id,
                pregunta,
                datetime.now(UTC),
                adjuntos,
            )
        except (AdjuntoNoSoportadoError, ValueError) as error:
            await ctx.send(str(error))
            return
        await ctx.send(texto)

    @bot.on_message_pattern(PATRON_AGENDA)
    async def responder_agenda(ctx: ActivityContext[MessageActivity]) -> None:
        if tiene_adjuntos(getattr(ctx.activity, "attachments", None) or []):
            await responder_chat(ctx)
            return
        await ctx.reply(TypingActivityInput())

        if not ctx.is_signed_in:
            # Honestidad antes que conveniencia: no se le sirven datos de
            # ejemplo a alguien que pidio SUS pendientes. Se le explica y
            # se le ofrece el boton.
            await ctx.send(NECESITO_PERMISO)
            await ctx.sign_in()
            return

        # Servicio construido POR PETICION, con el cliente de Graph de
        # ESTE usuario. Nunca cacheado: un servicio cacheado que lleva el
        # token de alguien le serviria sus datos al siguiente que pregunte.
        servicio_usuario = servicio_para_usuario(ctx.user_graph, _usuario_id(ctx), config)
        await ctx.send(await construir_respuesta_agenda(servicio_usuario, datetime.now(UTC)))

    @bot.on_message_pattern(PATRON_CONECTAR)
    async def conectar(ctx: ActivityContext[MessageActivity]) -> None:
        if ctx.is_signed_in:
            await ctx.send("Ya tienes tu cuenta conectada.")
            return
        await ctx.sign_in()

    @bot.on_message_pattern(PATRON_DESCONECTAR)
    async def desconectar(ctx: ActivityContext[MessageActivity]) -> None:
        await ctx.sign_out()
        await ctx.send("Listo, desconecté tu cuenta. Ya no tengo acceso a tus datos reales.")

    @bot.on_message_pattern(PATRON_ESTADO)
    async def estado(ctx: ActivityContext[MessageActivity]) -> None:
        # Nunca adivinar si lo que se muestra es real o de ejemplo: se
        # reporta lo que hay, de verdad, ahora mismo.
        if ctx.is_signed_in:
            await ctx.send("✅ Conectada. `semana` te muestra tus pendientes reales.")
        else:
            await ctx.send("⚪ No conectada. Escribe **`conectar`** para ver tus datos reales.")

    @bot.on_message_pattern(PATRON_AYUDA)
    async def responder_ayuda(ctx: ActivityContext[MessageActivity]) -> None:
        await ctx.send(AYUDA)

    @bot.on_message_pattern(PATRON_RECUERDAME)
    async def recuerdame(ctx: ActivityContext[MessageActivity]) -> None:
        """Anota un pendiente propio. Ejemplo: 'recuerdame entregar el informe el viernes'."""
        if not ctx.is_signed_in:
            await ctx.send(NECESITO_PERMISO)
            await ctx.sign_in()
            return

        await ctx.reply(TypingActivityInput())

        usuario = _usuario_id(ctx)
        svc = servicio_pendientes_propios_para_usuario(config, usuario)
        try:
            pendiente = await svc.recordar(ctx.activity.text or "", usuario, datetime.now(UTC))
            if pendiente.vence:
                fecha_str = f"vence el {pendiente.vence.strftime('%d/%m/%Y')}"
            else:
                fecha_str = "sin fecha asignada"
            await ctx.send(f"✅ Anotado: «{pendiente.titulo}», {fecha_str}.")
        except ValueError as e:
            await ctx.send(f"No entendí el pendiente: {e}")

    @bot.on_message_pattern(PATRON_OLVIDAR)
    async def olvidar(ctx: ActivityContext[MessageActivity]) -> None:
        try:
            await chat_general.olvidar(_usuario_id(ctx), ctx.activity.conversation.id)
        except (MemoriaNoDisponibleError, ValueError):
            await ctx.send("No pude borrar la memoria en este momento. Inténtalo otra vez.")
            return
        await ctx.send("Listo, borré lo que recordaba de esta conversación.")

    @bot.on_message
    async def pregunta_libre(ctx: ActivityContext[MessageActivity]) -> None:
        """Pregunta en lenguaje natural SOBRE LOS PENDIENTES del usuario.

        El handler no decide el alcance: se lo pregunta a
        `ServicioConversacion`, que solo le entrega al modelo la agenda de
        esta persona. Si la pregunta no va de pendientes, el servicio
        declina — y eso se puede testear sin Teams y sin gastar cuota.
        """
        mensaje = ctx.activity.text or ""
        attachments = getattr(ctx.activity, "attachments", None) or []
        if PATRON_CHAT.match(mensaje) or tiene_adjuntos(attachments):
            await responder_chat(ctx)
            return

        if not ctx.is_signed_in:
            # Sin sesion no hay agenda, y sin agenda no hay nada sobre lo
            # que responder. No se inventa ni se responde de cultura general.
            await ctx.send(NECESITO_PERMISO)
            await ctx.sign_in()
            return

        await ctx.reply(TypingActivityInput())
        texto = await construir_respuesta_libre(
            conversacion,
            servicio_para_usuario(ctx.user_graph, _usuario_id(ctx), config),
            ctx.activity.text or "",
            datetime.now(UTC),
        )
        await ctx.send(texto)

    return bot
