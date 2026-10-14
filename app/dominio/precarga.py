"""Estado mínimo de una precarga, sin conservar contenido de conversaciones."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EstadoPrecarga:
    """Metadatos para limitar frecuencia y detectar cambios de mensajes."""

    ultima_precarga_en: datetime
    huella_mensajes: str
