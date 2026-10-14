"""Cifrado de secretos persistentes antes de almacenarlos en Mongo."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.dominio.errores import ConfiguracionInvalidaError


class CifradorTokens:
    """Cifra refresh tokens; Mongo nunca recibe su valor legible."""

    def __init__(self, clave: str) -> None:
        if not clave:
            raise ConfiguracionInvalidaError(
                "BRUJULA_TOKEN_ENCRYPTION_KEY es obligatoria para la precarga"
            )

        try:
            self._fernet = Fernet(clave.encode("utf-8"))
        except (TypeError, ValueError) as error:
            raise ConfiguracionInvalidaError(
                "BRUJULA_TOKEN_ENCRYPTION_KEY no es una clave Fernet válida"
            ) from error

    def cifrar(self, secreto: str) -> str:
        """Convierte un secreto legible en texto seguro para Mongo."""
        if not secreto:
            raise ValueError("No se puede cifrar un secreto vacío")
        return self._fernet.encrypt(secreto.encode("utf-8")).decode("utf-8")

    def descifrar(self, secreto_cifrado: str) -> str:
        """Recupera el secreto solo dentro del proceso autorizado."""
        try:
            return self._fernet.decrypt(secreto_cifrado.encode("utf-8")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError) as error:
            raise ConfiguracionInvalidaError(
                "El token cifrado no se puede descifrar con la clave configurada"
            ) from error
