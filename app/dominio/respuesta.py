"""Lo que Nexo le contesta a una pregunta en lenguaje natural."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RespuestaAsistente:
    """Texto para el usuario, mas la trazabilidad de como se produjo.

    `modelo` no es telemetria: es honestidad. El usuario tiene derecho a
    saber si lo que lee lo escribio un modelo o lo compuso el sistema con
    datos estructurados. Es el mismo principio que `Pendiente.confianza`,
    aplicado a la respuesta entera.
    """

    texto: str
    modelo: str | None = None
    degradada: bool = False

    @property
    def generada_por_ia(self) -> bool:
        return self.modelo is not None

    def __post_init__(self) -> None:
        if not self.texto.strip():
            raise ValueError("RespuestaAsistente.texto no puede estar vacio")
