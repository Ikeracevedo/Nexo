"""Dominio: un archivo adjunto a un mensaje.

Solo libreria estandar (regla de app/dominio).
"""

from __future__ import annotations

from dataclasses import dataclass

MIME_DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
MIME_XLSX = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Tipos que el modelo lee directamente (se le envian tal cual).
MIMES_NATIVOS = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    }
)

MAX_BYTES_ADJUNTO = 10 * 1024 * 1024  # 10 MB por archivo


class AdjuntoNoSoportadoError(Exception):
    """El archivo no se puede leer. El mensaje es apto para mostrar al usuario."""


@dataclass(frozen=True, slots=True)
class Adjunto:
    nombre: str
    mime: str
    datos: bytes
