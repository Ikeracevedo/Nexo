"""El cifrado de refresh tokens se prueba sin Mongo ni OAuth."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.dominio.errores import ConfiguracionInvalidaError
from app.seguridad.cifrado import CifradorTokens


def test_cifra_y_descifra_sin_conservar_el_valor_legible() -> None:
    cifrador = CifradorTokens(Fernet.generate_key().decode("utf-8"))

    cifrado = cifrador.cifrar("refresh-token-secreto")

    assert cifrado != "refresh-token-secreto"
    assert cifrador.descifrar(cifrado) == "refresh-token-secreto"


def test_rechaza_clave_ausente() -> None:
    with pytest.raises(ConfiguracionInvalidaError, match="TOKEN_ENCRYPTION"):
        CifradorTokens("")


def test_no_descifra_un_token_con_otra_clave() -> None:
    primer_cifrador = CifradorTokens(Fernet.generate_key().decode("utf-8"))
    segundo_cifrador = CifradorTokens(Fernet.generate_key().decode("utf-8"))

    with pytest.raises(ConfiguracionInvalidaError, match="no se puede descifrar"):
        segundo_cifrador.descifrar(primer_cifrador.cifrar("secreto"))
