"""Proveedor de LLM determinista para tests (ADR-006).

NO es un LLM pequeno ni un modelo local: son veinte lineas que devuelven
una cadena fija. Determinista porque un test afirma "esta entrada produce
exactamente esta salida"; con salida variable los tests fallan al azar, y
el rojo intermitente ensena a ignorar el rojo.

Corre en milisegundos, sin red, sin cuota y sin API key: por eso el CI
puede ejercitar el camino completo de conversacion sin secretos.
"""

from __future__ import annotations

from app.dominio.errores import LLMNoDisponibleError


class FakeLLMProvider:
    """Implementa LLMProvider sin importarlo (tipado estructural)."""

    def __init__(self, respuesta: str = "Respuesta de prueba.", fallar: bool = False) -> None:
        self._respuesta = respuesta
        self._fallar = fallar
        self.ultima_instruccion: str | None = None
        self.ultimo_contexto: str | None = None
        self.llamadas = 0

    @property
    def nombre_modelo(self) -> str:
        return "fake-llm"

    async def generar(self, instruccion: str, contexto: str) -> str:
        # Se guardan para que un test pueda afirmar QUE se le mando al
        # modelo. Es la unica forma de verificar que el contexto que sale
        # de Nexo es la agenda y no texto arbitrario del usuario.
        self.ultima_instruccion = instruccion
        self.ultimo_contexto = contexto
        self.llamadas += 1
        if self._fallar:
            raise LLMNoDisponibleError(self.nombre_modelo, "fallo simulado")
        return self._respuesta
