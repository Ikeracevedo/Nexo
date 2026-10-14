"""Dependencias del canal HTTP.

El canal HTTP no tiene (todavia) usuario autenticado: `/api/agenda`
sirve el MODO DEMO con datos de ejemplo. Cuando en F4 exista el
frontend web con su propio inicio de sesion, este archivo pasara a
construir el servicio con las fuentes reales de ese usuario, igual que
hace hoy el canal de Teams.

Se mantiene `lru_cache` porque `FuenteEjemplo` no tiene estado de
usuario. En el canal de Teams NO se cachea, y esa diferencia es
deliberada: cachear un servicio que lleva el token de alguien seria
servirle a un usuario los datos de otro.
"""

from __future__ import annotations

from functools import lru_cache

from app.composicion import servicio_autorizacion_graph, servicio_de_ejemplo
from app.config import obtener_configuracion
from app.servicios.servicio_agenda import ServicioAgenda
from app.servicios.servicio_autorizacion_graph import ServicioAutorizacionGraph


@lru_cache
def obtener_servicio_agenda() -> ServicioAgenda:
    return servicio_de_ejemplo()


def obtener_servicio_autorizacion_graph() -> ServicioAutorizacionGraph:
    """Construye OAuth por solicitud; nunca conserva estado de un usuario."""
    return servicio_autorizacion_graph(obtener_configuracion())
