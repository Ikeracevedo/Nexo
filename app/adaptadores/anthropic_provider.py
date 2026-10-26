"""Adaptador Anthropic detras del puerto ``LLMProvider``."""

from __future__ import annotations

import base64
import logging
from collections.abc import Sequence
from typing import Any

from app.config import Configuracion
from app.dominio.adjunto import Adjunto
from app.dominio.errores import LLMNoDisponibleError

logger = logging.getLogger(__name__)

PROVEEDOR = "anthropic"
TIMEOUT_SEGUNDOS = 20.0
MAX_TOKENS_RESPUESTA = 1024


class AnthropicProvider:
    """Implementa texto, imagenes y PDF con la Messages API de Anthropic."""

    def __init__(self, configuracion: Configuracion) -> None:
        self._config = configuracion
        self._cliente: Any | None = None

    @property
    def nombre_modelo(self) -> str:
        return self._config.anthropic_modelo

    @property
    def esta_configurado(self) -> bool:
        return bool(self._config.anthropic_api_key)

    def _obtener_cliente(self) -> Any:
        if self._cliente is None:
            if not self._config.anthropic_api_key:
                raise LLMNoDisponibleError(PROVEEDOR, "ANTHROPIC_API_KEY no esta configurada")
            from anthropic import AsyncAnthropic

            self._cliente = AsyncAnthropic(api_key=self._config.anthropic_api_key)
        return self._cliente

    async def generar(self, instruccion: str, contexto: str) -> str:
        return await self._generar(instruccion, [{"type": "text", "text": contexto}])

    async def generar_con_adjuntos(
        self, instruccion: str, contexto: str, adjuntos: Sequence[Adjunto]
    ) -> str:
        contenido: list[dict[str, object]] = [
            {
                "type": "document" if adjunto.mime == "application/pdf" else "image",
                "source": {
                    "type": "base64",
                    "media_type": adjunto.mime,
                    "data": base64.b64encode(adjunto.datos).decode("ascii"),
                },
            }
            for adjunto in adjuntos
        ]
        contenido.append({"type": "text", "text": contexto})
        return await self._generar(instruccion, contenido)

    async def _generar(self, instruccion: str, contenido: list[dict[str, object]]) -> str:
        try:
            respuesta = await self._obtener_cliente().messages.create(
                model=self.nombre_modelo,
                max_tokens=MAX_TOKENS_RESPUESTA,
                system=instruccion,
                messages=[{"role": "user", "content": contenido}],
                timeout=TIMEOUT_SEGUNDOS,
            )
        except LLMNoDisponibleError:
            raise
        except Exception as error:
            logger.warning("Anthropic fallo: %s: %s", type(error).__name__, error)
            raise LLMNoDisponibleError(PROVEEDOR, type(error).__name__) from error

        texto = "".join(
            bloque.text
            for bloque in getattr(respuesta, "content", [])
            if isinstance(getattr(bloque, "text", None), str)
        ).strip()
        if not texto:
            raise LLMNoDisponibleError(PROVEEDOR, "respuesta sin texto")
        return texto
