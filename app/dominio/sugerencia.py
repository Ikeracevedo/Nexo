"""Modelo de una posible tarea inferida desde una conversación.

Una sugerencia nunca es un Pendiente: requiere confirmación humana antes de
entrar a la agenda. Conserva trazabilidad al mensaje, no su cuerpo original.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class DeQuien(StrEnum):
    """Persona que expresó el compromiso detectado."""

    USUARIO = "usuario"
    OTRO = "otro"


class EstadoSugerencia(StrEnum):
    """Ciclo de vida de una sugerencia inferida."""

    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    DESCARTADA = "descartada"


@dataclass(frozen=True, slots=True)
class Sugerencia:
    """Compromiso propuesto por IA, pendiente de decisión del usuario."""

    texto: str
    confianza: float
    id_mensaje: str
    url_mensaje: str
    conversacion: str
    de_quien: DeQuien
    fecha: date | None = None
    id: str | None = None
    estado: EstadoSugerencia = EstadoSugerencia.PENDIENTE

    def __post_init__(self) -> None:
        if not self.texto.strip():
            raise ValueError("Sugerencia.texto no puede estar vacio")
        if not self.id_mensaje.strip():
            raise ValueError("Sugerencia.id_mensaje no puede estar vacio")
        if not self.url_mensaje.strip():
            raise ValueError("Sugerencia.url_mensaje no puede estar vacio")
        if not self.conversacion.strip():
            raise ValueError("Sugerencia.conversacion no puede estar vacio")
        if self.id is not None and not self.id.strip():
            raise ValueError("Sugerencia.id no puede estar vacio")
        if not 0.0 <= self.confianza <= 1.0:
            raise ValueError("Sugerencia.confianza debe estar entre 0 y 1")
