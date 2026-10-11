"""Composición de las implementaciones concretas de Brújula."""

from __future__ import annotations

from typing import Any

from app.adaptadores.extractor_docx import ExtractorDocx
from app.adaptadores.extractor_xlsx import ExtractorXlsx
from app.adaptadores.fuente_ejemplo import FuenteEjemplo
from app.adaptadores.gemini_provider import GeminiProvider
from app.adaptadores.graph_calendario import FuenteCalendarioGraph
from app.adaptadores.memoria_en_proceso import MemoriaEnProceso
from app.adaptadores.memoria_mongo import MemoriaMongo
from app.config import Configuracion
from app.puertos.llm_provider import LLMProvider
from app.puertos.memoria_conversacion import MemoriaConversacion
from app.puertos.task_source import TaskSource
from app.servicios.servicio_agenda import ServicioAgenda
from app.servicios.servicio_conversacion import ServicioConversacion


def servicio_de_ejemplo() -> ServicioAgenda:
    """Modo demo: datos fijos, sin red y sin usuario."""
    fuentes: list[TaskSource] = [FuenteEjemplo()]
    return ServicioAgenda(fuentes)


def servicio_para_usuario(cliente_graph: Any) -> ServicioAgenda:
    """Modo real: las fuentes de ESTE usuario, con SU cliente de Graph."""
    fuentes: list[TaskSource] = [FuenteCalendarioGraph(cliente_graph)]
    return ServicioAgenda(fuentes)


def proveedor_gemini(config: Configuracion) -> LLMProvider:
    """Construye el proveedor de Gemini."""
    return GeminiProvider(config)


def memoria_de_conversacion(config: Configuracion) -> MemoriaConversacion:
    """Mongo si hay URI; si no, RAM (se pierde al reiniciar)."""
    if config.mongodb_uri:
        return MemoriaMongo(config.mongodb_uri)
    return MemoriaEnProceso()


def servicio_conversacion(config: Configuracion) -> ServicioConversacion:
    """Chat con Gemini: memoria por conversación y lectura de Word y Excel."""
    return ServicioConversacion(
        llm=proveedor_gemini(config),
        memoria=memoria_de_conversacion(config),
        extractor_docx=ExtractorDocx(),
        extractor_xlsx=ExtractorXlsx(),
    )