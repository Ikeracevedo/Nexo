"""

Adaptador secundatio de enventos de calendarios de Microsft Graph

Adaptador: implementa el puerto TaskSource sin importarlo, igual que la
fuente hardcodeada de ejemplo.
Recibe el cliente de Graph ya autenticado, no sabe de donde sale el token, ni nada de infrastructura
Solo sabe pedir los eventos a la API Graph y traducirlos a los dominios

"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.users.item.calendar_view.calendar_view_request_builder import (
    CalendarViewRequestBuilder,
)

from app.dominio.errores import FuenteNoDisponibleError, FuenteSinPermisoError
from app.dominio.pendiente import FuentePendiente, Pendiente

logger = logging.getLogger(__name__)

NOMBRE = "calendario"
PERMISO = "Calendars.Read"

# Enlace generico al calendario del usuario solo se usa cuando graph falla
# ENlace directo pero sigue siendo veridico
URL_CALENDARIO = "https://outlook.office.com/calendar/"


class FuenteCalendarioGraph:
    """Lee /me/calendarView en la ventana perdida"""

    def __init__(self, cliente_graph: Any) -> None:
        self._graph = cliente_graph

    @property
    def nombre(self) -> str:
        return NOMBRE

    async def obtener_pendientes(self, desde: datetime, hasta: datetime) -> list[Pendiente]:
        try:
            respuesta = await self._graph.me.calendar_view.get(
                request_configuration=self._configuracion(desde, hasta)
            )
        except Exception as e:  # se reclasifica abajo; no se traga ningun error
            logger.exception("Error al llamar a Graph API: %s", e)
            raise self._traducir_error(e) from e

        eventos = getattr(respuesta, "value", None) or []
        return [p for p in (self._a_pendiente(ev) for ev in eventos) if p is not None]

    @staticmethod
    def _configuracion(desde: datetime, hasta: datetime) -> Any:
        # `calendarView` (y no `/me/events`) porque expande series recurrentes
        # dentro de la ventana. Con /me/events, una clase semanal aparece una
        # sola vez, en su fecha original, y el usuario no la ve esta semana.
        query_params = CalendarViewRequestBuilder.CalendarViewRequestBuilderGetQueryParameters(
            start_date_time=desde.isoformat(), end_date_time=hasta.isoformat()
        )
        return RequestConfiguration(
            headers={"Prefer": 'outlook.timezone="UTC"'},
            query_parameters=query_params,
        )

    @staticmethod
    def _traducir_error(e: Exception) -> FuenteNoDisponibleError:
        """Normaliza el error de Graph a un error del dominio.

        REGLA DE OT-01: un fallo nunca se traduce a lista vacia.
        Aqui ademas se separa el 401/403 (accion: iniciar sesion) del
        resto (accion: reintentar o avisar).
        """
        codigo = getattr(e, "response_status_code", None)
        if codigo in (401, 403):
            return FuenteSinPermisoError(NOMBRE, PERMISO)
        return FuenteNoDisponibleError(NOMBRE, f"Graph respondio {codigo or type(e).__name__}")

    @staticmethod
    def _a_pendiente(evento: Any) -> Pendiente | None:
        inicio = getattr(getattr(evento, "start", None), "date_time", None)
        vence: datetime | None = None
        if inicio:
            try:
                vence = datetime.fromisoformat(str(inicio).replace("Z", "+00:00"))
                if vence.tzinfo is None:
                    vence = vence.replace(tzinfo=UTC)
            except ValueError:
                logger.warning(
                    "Evento %s con fecha ilegible: %r", getattr(evento, "id", "?"), inicio
                )

        identificador = getattr(evento, "id", None)
        titulo = (getattr(evento, "subject", None) or "").strip()
        if not identificador or not titulo:
            # Sin id o sin titulo no se puede construir un Pendiente valido.
            # Se descarta ESTE evento y se registra; no se rompe la agenda entera.
            logger.warning("Evento de calendario descartado por incompleto: id=%r", identificador)
            return None

        return Pendiente(
            id=f"cal-{identificador}",
            titulo=titulo,
            fuente=FuentePendiente.CALENDARIO,
            url_origen=getattr(evento, "web_link", None) or URL_CALENDARIO,
            vence=vence,
            confianza=1.0,
        )
