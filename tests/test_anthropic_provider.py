from __future__ import annotations

import asyncio
import base64
from typing import Any

import pytest

from app.adaptadores.anthropic_provider import AnthropicProvider
from app.composicion import proveedor_llm
from app.config import Configuracion
from app.dominio.adjunto import Adjunto
from app.dominio.errores import LLMNoDisponibleError


def _config(**kwargs: Any) -> Configuracion:
    return Configuracion(**kwargs)


def test_se_puede_construir_sin_api_key() -> None:
    proveedor = AnthropicProvider(_config(anthropic_api_key=""))
    assert proveedor.esta_configurado is False


def test_sin_api_key_falla_al_usarlo_no_al_crearlo() -> None:
    proveedor = AnthropicProvider(_config(anthropic_api_key=""))
    with pytest.raises(LLMNoDisponibleError) as error:
        asyncio.run(proveedor.generar("instruccion", "contexto"))
    assert error.value.proveedor == "anthropic"
    assert "ANTHROPIC_API_KEY" in error.value.motivo


def test_modelo_y_proveedor_salen_de_configuracion() -> None:
    config = _config(llm_proveedor="anthropic", anthropic_modelo="claude-haiku-prueba")
    proveedor = proveedor_llm(config)
    assert isinstance(proveedor, AnthropicProvider)
    assert proveedor.nombre_modelo == "claude-haiku-prueba"


async def test_envia_adjuntos_en_formato_messages_sin_red() -> None:
    class Mensajes:
        def __init__(self) -> None:
            self.argumentos: dict[str, Any] = {}

        async def create(self, **kwargs: Any) -> Any:
            self.argumentos = kwargs
            bloque = type("Bloque", (), {"text": "Respuesta de Claude"})()
            return type("Respuesta", (), {"content": [bloque]})()

    mensajes = Mensajes()
    proveedor = AnthropicProvider(_config(anthropic_api_key="clave-de-prueba"))
    proveedor._cliente = type("Cliente", (), {"messages": mensajes})()
    imagen = Adjunto("pizarra.png", "image/png", b"imagen-de-prueba")

    respuesta = await proveedor.generar_con_adjuntos("sistema", "Que ves?", [imagen])

    assert respuesta == "Respuesta de Claude"
    assert mensajes.argumentos["system"] == "sistema"
    contenido = mensajes.argumentos["messages"][0]["content"]
    assert contenido[0] == {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64.b64encode(imagen.datos).decode("ascii"),
        },
    }
    assert contenido[1] == {"type": "text", "text": "Que ves?"}
