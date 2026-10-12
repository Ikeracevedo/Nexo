"""Adaptador SECUNDARIO: Google Gemini detras del puerto `LLMProvider`.

Basado en el trabajo de Julian Gomez (rama `feature/gemini`, 20-sep-2026).
La llamada a la API es la suya y esta verificada contra `google-genai 2.23.0`:
`client.aio.interactions.create(...)` existe y su respuesta trae `output_text`.

Cambios respecto a su version, y por que:

1. **El cliente se construye perezosamente.** Su version hacia `raise` en
   `__init__` si faltaba la API key, y `crear_bot_teams` lo construia al
   importar `app.main`. Resultado medido: sin `GEMINI_API_KEY` la aplicacion
   entera no arrancaba —ni `/health`, que no usa Gemini— y `pytest` pasaba de
   69 tests a **cero** por error de recoleccion. Una funcion opcional no puede
   ser un requisito de arranque.
2. **El modelo sale de la configuracion.** Estaba fijo en el codigo. Cambiar de
   modelo es exactamente lo que el ADR-006 queria que costara una variable de
   entorno.
3. **Se normaliza el error** a `LLMNoDisponibleError` en vez de propagar la
   excepcion cruda del SDK. Si el nucleo tuviera que capturar errores de
   `google.genai`, el puerto no habria servido de nada.
4. **Timeout explicito.** Sin el, una llamada colgada cuelga el handler del bot
   y Teams reintenta (ADR-008: nadie espera 15 segundos por un mensaje).
"""

from __future__ import annotations

import base64
import logging
from collections.abc import Sequence
from typing import Any

from app.config import Configuracion
from app.dominio.adjunto import Adjunto
from app.dominio.errores import LLMNoDisponibleError

logger = logging.getLogger(__name__)

PROVEEDOR = "gemini"
TIMEOUT_SEGUNDOS = 20.0


class GeminiProvider:
    """Implementa `LLMProvider` sin importarlo (tipado estructural)."""

    def __init__(self, configuracion: Configuracion) -> None:
        self._config = configuracion
        self._cliente: Any | None = None

    @property
    def nombre_modelo(self) -> str:
        return self._config.gemini_modelo

    @property
    def esta_configurado(self) -> bool:
        """Permite que `estado` le diga la verdad al usuario sin llamar a la API."""
        return bool(self._config.gemini_api_key)

    def _obtener_cliente(self) -> Any:
        if self._cliente is None:
            if not self._config.gemini_api_key:
                raise LLMNoDisponibleError(PROVEEDOR, "GEMINI_API_KEY no esta configurada")
            from google import genai  # import perezoso: no encarece el arranque

            self._cliente = genai.Client(api_key=self._config.gemini_api_key)
        return self._cliente

    async def generar(self, instruccion: str, contexto: str) -> str:
        return await self._generar(instruccion, contexto)

    async def generar_con_adjuntos(
        self, instruccion: str, contexto: str, adjuntos: Sequence[Adjunto]
    ) -> str:
        """Envía imágenes y PDF a Gemini sin alterar el puerto de texto de la agenda."""
        entrada = [
            *(
                {
                    "type": "image" if adjunto.mime.startswith("image/") else "document",
                    "data": base64.b64encode(adjunto.datos).decode("ascii"),
                    "mime_type": adjunto.mime,
                }
                for adjunto in adjuntos
            ),
            {"type": "text", "text": contexto},
        ]
        return await self._generar(instruccion, entrada)

    async def _generar(self, instruccion: str, entrada: Any) -> str:
        cliente = self._obtener_cliente()
        try:
            respuesta = await cliente.aio.interactions.create(
                model=self.nombre_modelo,
                system_instruction=instruccion,
                input=entrada,
                timeout=TIMEOUT_SEGUNDOS,
            )
        except LLMNoDisponibleError:
            raise
        except Exception as e:
            # Se normaliza, no se traga: el motivo viaja hasta el servicio,
            # que decide que ve el usuario. Nada se silencia.
            logger.warning("Gemini fallo: %s: %s", type(e).__name__, e)
            raise LLMNoDisponibleError(PROVEEDOR, f"{type(e).__name__}") from e

        # `interactions.create` devuelve `Interaction | AsyncStream[...]`.
        # No pedimos streaming, asi que esperamos `Interaction`; se comprueba
        # en vez de asumirlo, porque un cambio del SDK aqui seria silencioso.
        salida = getattr(respuesta, "output_text", None)
        if not isinstance(salida, str):
            raise LLMNoDisponibleError(
                PROVEEDOR, f"respuesta sin texto ({type(respuesta).__name__})"
            )
        return salida
