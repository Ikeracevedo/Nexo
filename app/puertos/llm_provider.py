"""Puerto: contrato de un proveedor de modelo de lenguaje


Implementaciones previstas:
  - FakeLLMProvider  -> determinista, para tests. Sin red, sin costo.
  - GeminiProvider   -> Gemini API (proveedor confirmado en OT-01).
  - AnthropicProvider -> Claude API, seleccionable por configuracion.
  - OllamaProvider   -> local, sin conexion ni cuota.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    @property
    def nombre_modelo(self) -> str:
        """Identificador del modelo. Se registra junto a cada respuesta
        para poder auditar despues con que modelo se genero."""
        ...

    async def generar(self, instruccion: str, contexto: str) -> str:
        """Genera texto a partir de una instruccion y un contexto.

        instruccion: que debe hacer el modelo (el 'system prompt').
        contexto:    los datos sobre los que trabajar.

        Se mantienen separados A PROPOSITO: mezclarlos en una sola
        cadena es la puerta de entrada de la prompt injection — si
        la interfaz solo aceptara un string, esa frontera no existiria.
        """
