"""Canal HTTP/REST: adaptador PRIMARIO sobre el nucleo.

Expone un APIRouter, no una app. Quien construye la app y decide que
canales se montan es el composition root
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.api.dependencias import (
    obtener_servicio_agenda,
    obtener_servicio_autorizacion_graph,
)
from app.api.esquemas import AgendaDTO, SaludDTO
from app.api.pagina_inicio import PAGINA_INICIO
from app.config import obtener_configuracion
from app.dominio.errores import NexoError
from app.servicios.servicio_agenda import ServicioAgenda
from app.servicios.servicio_autorizacion_graph import ServicioAutorizacionGraph

VERSION = "0.2.0"

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def pagina_inicio() -> HTMLResponse:
    """Presenta Nexo y explica el primer paso dentro de Teams."""
    return HTMLResponse(PAGINA_INICIO)


@router.get("/health", response_model=SaludDTO, tags=["operacion"])
async def health() -> SaludDTO:
    config = obtener_configuracion()
    return SaludDTO(estado="ok", version=VERSION, entorno=config.brujula_entorno)


@router.get("/api/agenda", response_model=AgendaDTO, tags=["agenda"])
async def obtener_agenda(
    servicio: Annotated[ServicioAgenda, Depends(obtener_servicio_agenda)],
) -> AgendaDTO:
    """Este endpoint y el handler `semana` del bot llaman al MISMO
    ServicioAgenda. Dos canales, cero logica duplicada."""
    agenda = await servicio.pendientes_de_la_semana(datetime.now(UTC))
    return AgendaDTO.desde_dominio(agenda)


@router.get("/auth/callback", response_class=HTMLResponse, include_in_schema=False)
async def completar_autorizacion_graph(
    servicio: Annotated[ServicioAutorizacionGraph, Depends(obtener_servicio_autorizacion_graph)],
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> HTMLResponse:
    """Recibe el retorno de Entra sin exponer tokens ni datos del usuario."""
    if error or not code or not state:
        raise HTTPException(status_code=400, detail="No se completó la autorización de Microsoft.")
    try:
        await servicio.completar(state, code, datetime.now(UTC))
    except NexoError as error_autorizacion:
        raise HTTPException(
            status_code=400, detail="No se pudo conectar la cuenta."
        ) from error_autorizacion
    return HTMLResponse(
        "<h1>Cuenta conectada</h1><p>Ya puedes volver a Teams y escribir <code>revisar</code>.</p>"
    )
