"""Composicion: que fuentes se consultan, y para quien.

Vive en la raiz de `app/`, NO en `app/servicios/`. Primer intento lo puso
alli y `test_servicios_no_conoce_adaptadores_ni_api` lo rechazo al
instante: un servicio depende de puertos, nunca de implementaciones.
Ensamblar implementaciones concretas es trabajo del composition root.

Antes de OT-04 el sistema tenia UN juego de fuentes para todo el mundo,
construido una sola vez (`lru_cache`). Con datos reales eso deja de ser
valido: las fuentes de Iker no son las de otro usuario, porque llevan
SU token. El servicio pasa a construirse por peticion.

> Regla general: un singleton solo es correcto mientras el objeto no
> tenga estado propio del usuario. En cuanto lo tiene, cachearlo deja de
> ser una optimizacion y pasa a ser una fuga de datos entre usuarios.
"""

from __future__ import annotations

from typing import Any
from zoneinfo import ZoneInfo

from app.adaptadores.credenciales_graph_mongo import CredencialesGraphMongo
from app.adaptadores.estado_oauth_mongo import EstadoOAuthMongo
from app.adaptadores.estado_precarga_mongo import EstadoPrecargaMongo
from app.adaptadores.extractor_docx import ExtractorDocx
from app.adaptadores.extractor_xlsx import ExtractorXlsx
from app.adaptadores.fabrica_graph_precarga import FabricaFuenteChatsGraph
from app.adaptadores.fuente_ejemplo import FuenteEjemplo
from app.adaptadores.gemini_provider import GeminiProvider
from app.adaptadores.graph_calendario import FuenteCalendarioGraph
from app.adaptadores.graph_chats import FuenteChatsGraph
from app.adaptadores.graph_planner import FuentePlannerGraph
from app.adaptadores.graph_todo import FuenteToDoGraph
from app.adaptadores.memoria_en_proceso import MemoriaEnProceso
from app.adaptadores.memoria_mongo import MemoriaMongo
from app.adaptadores.mongo_pendientes import FuentePropiaMongo
from app.adaptadores.oauth_graph_entra import IntercambiadorCodigoEntra
from app.adaptadores.preferencias_mongo import PreferenciasMongo
from app.adaptadores.sugerencias_mongo import SugerenciasMongo
from app.config import Configuracion
from app.puertos.fuente_mensajes import FuenteMensajes
from app.puertos.llm_provider import LLMProvider
from app.puertos.task_source import TaskSource
from app.servicios.servicio_agenda import ServicioAgenda
from app.servicios.servicio_autorizacion_graph import ServicioAutorizacionGraph
from app.servicios.servicio_chat_general import ServicioChatGeneral
from app.servicios.servicio_conversacion import ServicioConversacion
from app.servicios.servicio_deteccion import ServicioDeteccion
from app.servicios.servicio_pendientes_propios import ServicioPendientesPropios
from app.servicios.servicio_precarga import ServicioPrecarga
from app.servicios.servicio_sugerencias import ServicioSugerencias
from app.servicios.servicio_vigilancia import ServicioVigilancia


def servicio_de_ejemplo() -> ServicioAgenda:
    """Modo demo: datos fijos, sin red y sin usuario. Lo usa el canal HTTP."""
    fuentes: list[TaskSource] = [FuenteEjemplo()]
    return ServicioAgenda(fuentes)


def servicio_para_usuario(
    cliente_graph: Any,
    usuario_id: str,
    config: Configuracion,
) -> ServicioAgenda:
    """Modo real: las cuatro fuentes de ESTE usuario, con SU cliente de Graph.

    El diff entre OT-04 (1 fuente) y OT-05 (4 fuentes) es esta funcion.
    ServicioAgenda, Agenda y ServicioConversacion no cambiaron una linea.
    Esa es la promesa de la arquitectura hexagonal: anadir un origen de
    datos cuesta un archivo nuevo y dos lineas aqui.
    """
    fuente_mongo = FuentePropiaMongo(config, usuario_id)
    fuentes: list[TaskSource] = [
        FuenteCalendarioGraph(cliente_graph),
        FuenteToDoGraph(cliente_graph),
        FuentePlannerGraph(cliente_graph, config.azure_tenant_id),
        fuente_mongo,
    ]
    return ServicioAgenda(fuentes)


def servicio_pendientes_propios_para_usuario(
    config: Configuracion,
    usuario_id: str,
) -> ServicioPendientesPropios:
    """Servicio de escritura para el comando 'recuerdame'.

    Crea una FuentePropiaMongo independiente: el composition root ensambla,
    no reutiliza por accidente el mismo objeto del servicio de lectura.
    """
    return ServicioPendientesPropios(FuentePropiaMongo(config, usuario_id))


def servicio_vigilancia(config: Configuracion) -> ServicioVigilancia:
    """Servicio para el consentimiento de vigilancia de conversaciones."""
    return ServicioVigilancia(PreferenciasMongo(config), CredencialesGraphMongo(config))


def servicio_autorizacion_graph(config: Configuracion) -> ServicioAutorizacionGraph:
    """Ensambla OAuth solo al usarlo, para no exigir secretos al arranque."""
    return ServicioAutorizacionGraph(
        config,
        EstadoOAuthMongo(config),
        IntercambiadorCodigoEntra(config),
        CredencialesGraphMongo(config),
        PreferenciasMongo(config),
    )


def servicio_precarga(config: Configuracion) -> ServicioPrecarga:
    """Ensambla el worker sin compartir clientes ni credenciales entre usuarios."""
    return ServicioPrecarga(
        PreferenciasMongo(config),
        CredencialesGraphMongo(config),
        IntercambiadorCodigoEntra(config),
        FabricaFuenteChatsGraph(config.teams_bot_id),
        servicio_deteccion(config),
        SugerenciasMongo(config),
        EstadoPrecargaMongo(config),
    )


def fuente_mensajes_para_usuario(
    cliente_graph: Any,
    usuario_id: str,
    config: Configuracion,
) -> FuenteMensajes:
    """Construye la fuente de chats para un usuario y token concretos."""
    return FuenteChatsGraph(cliente_graph, usuario_id, config.teams_bot_id)


def servicio_deteccion(config: Configuracion) -> ServicioDeteccion:
    """Construye el detector con el proveedor LLM configurado."""
    return ServicioDeteccion(proveedor_llm(config))


def proveedor_llm(config: Configuracion) -> LLMProvider:
    """El proveedor de LLM del sistema.

    Cambiar Gemini por Ollama o por OpenAI es cambiar ESTA linea: el resto
    del sistema habla con el puerto. Es la promesa del ADR-006, en un sitio
    donde se puede comprobar con un `git diff`.
    """
    return GeminiProvider(config)


def servicio_conversacion(config: Configuracion) -> ServicioConversacion:
    """El caso de uso de conversacion, con su proveedor ya inyectado."""
    return ServicioConversacion(
        proveedor_llm(config), ZoneInfo(config.brujula_zona_horaria), config.bot_nombre
    )


def servicio_chat_general(config: Configuracion) -> ServicioChatGeneral:
    """Chat de Julián con memoria; el modo local usa RAM si no hay Mongo."""
    memoria = MemoriaMongo(config.mongodb_uri) if config.mongodb_uri else MemoriaEnProceso()
    return ServicioChatGeneral(
        GeminiProvider(config),
        memoria,
        extractor_docx=ExtractorDocx(),
        extractor_xlsx=ExtractorXlsx(),
        nombre=config.bot_nombre,
    )


def servicio_sugerencias_para_usuario(
    config: Configuracion,
    usuario_id: str,
) -> ServicioSugerencias:
    """Construye bandeja y pendientes propios para un usuario aislado."""
    return ServicioSugerencias(
        SugerenciasMongo(config),
        FuentePropiaMongo(config, usuario_id),
    )
