from __future__ import annotations

from datetime import datetime, timedelta

from app.dominio.pendiente import FuentePendiente, Pendiente

_BASE = "https://teams.microsoft.com/l/entity/ejemplo"


class FuenteEjemplo:
    """Implementa TaskSource sin heredar de el (tipado estructural)."""

    @property
    def nombre(self) -> str:
        return "ejemplo"

    async def obtener_pendientes(
        self,
        desde: datetime,
        hasta: datetime,
    ) -> list[Pendiente]:
        todos = self._datos(desde)
        # Filtra a la ventana pedida. Sin fecha (vence=None) siempre pasa,
        # porque una tarea sin vencimiento no se puede excluir por fecha.
        return [p for p in todos if p.vence is None or desde <= p.vence <= hasta]

    @staticmethod
    def _datos(referencia: datetime) -> list[Pendiente]:
        return [
            Pendiente(
                id="ej-planner-1",
                titulo="Entregar avance del proyecto integrador",
                fuente=FuentePendiente.PLANNER,
                url_origen=f"{_BASE}/planner/1",
                vence=referencia + timedelta(days=2),
                confianza=1.0,
            ),
            Pendiente(
                id="ej-todo-1",
                titulo="Leer capitulo 4 de arquitectura de software",
                fuente=FuentePendiente.TODO,
                url_origen=f"{_BASE}/todo/1",
                vence=referencia + timedelta(days=3),
                confianza=1.0,
            ),
            Pendiente(
                id="ej-cal-1",
                titulo="Sustentacion parcial - Proyecto en TIC 1",
                fuente=FuentePendiente.CALENDARIO,
                url_origen=f"{_BASE}/calendario/1",
                vence=referencia + timedelta(days=5),
                confianza=1.0,
            ),
            Pendiente(
                id="ej-msg-1",
                titulo="Posible entrega de laboratorio mencionada en el canal",
                fuente=FuentePendiente.MENSAJE,
                url_origen=f"{_BASE}/mensaje/1",
                vence=referencia + timedelta(days=4),
                confianza=0.72,
                contexto=(
                    "Inferido de un mensaje del canal. "
                    "Nexo no confirma este pendiente: verificalo en el origen."
                ),
            ),
        ]
