from __future__ import annotations


class NexoError(Exception):
    """
    Raiz de todos los errores propios

    Permite capturar el dominio entero sin arapar por accidente
    ValueError o KeyError ajeno, que son bugs y deben explotar
    """


class FuenteNoDisponibleError(NexoError):
    """
    Una fuente no pudo ser consultada. NO significa 'sin pendientes'.
    """

    def __init__(self, nombre_fuente: str, motivo: str) -> None:
        # Se guardan como atributis no solo dentro del texto del mensaje
        # El servicio los lee para construir FuenteFallida
        self.nombre_fuente = nombre_fuente
        self.motivo = motivo
        super().__init__(f"No se pudo consultar '{nombre_fuente}': {motivo}")


class ConfiguracionInvalidaError(NexoError):
    """Falta una variable de entorno obligatoria o tiene un valor imposible."""


class FuenteSinPermisoError(FuenteNoDisponibleError):
    """El usuario no ha autorizado (o revoco) el permiso para esta fuente.

    Es un subtipo de FuenteNoDisponibleError a proposito: el servicio ya
    sabe tratarlo sin cambiar una linea. Pero se distingue porque tiene
    una ACCION asociada distinta: un 403 por permisos se arregla
    iniciando sesion; un 500 de Graph, no. La tarjeta puede ofrecer
    "Conectar mi cuenta" solo cuando el fallo es de este tipo.
    """

    def __init__(self, nombre_fuente: str, permiso_requerido: str) -> None:
        self.permiso_requerido = permiso_requerido
        super().__init__(nombre_fuente, f"falta el permiso '{permiso_requerido}'")


class LLMNoDisponibleError(NexoError):
    """El proveedor de modelo de lenguaje no pudo responder.

    Mismo principio que FuenteNoDisponibleError: un fallo del LLM NO se
    traduce en una respuesta inventada ni en silencio. Se declara, y la
    capa de arriba decide que decirle al usuario.
    """

    def __init__(self, proveedor: str, motivo: str) -> None:
        self.proveedor = proveedor
        self.motivo = motivo
        super().__init__(f"El proveedor '{proveedor}' no pudo responder: {motivo}")
