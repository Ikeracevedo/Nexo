"""Puerto: extraccion de texto de documentos que el modelo no lee directo.

Implementaciones:
  - ExtractorDocx -> archivos Word (.docx) con python-docx.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ExtractorTexto(Protocol):
    def extraer_texto(self, datos: bytes) -> str:
        """Devuelve el texto plano del documento."""
        ...
