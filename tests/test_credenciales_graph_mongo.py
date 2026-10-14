"""Pruebas del almacén cifrado de credenciales renovables."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from cryptography.fernet import Fernet

from app.adaptadores.credenciales_graph_mongo import CredencialesGraphMongo
from app.config import Configuracion
from app.seguridad.cifrado import CifradorTokens

USUARIO = "usuario-aad"
OTRO_USUARIO = "otro-aad"
TOKEN = "refresh-token-secreto"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)
CLAVE = Fernet.generate_key().decode()


class _ColeccionFalsa:
    def __init__(self, documentos: list[dict[str, Any]] | None = None) -> None:
        self.documentos = documentos or []
        self.ultimo_filtro: dict[str, Any] | None = None

    async def update_one(
        self,
        filtro: dict[str, Any],
        actualizacion: dict[str, Any],
        upsert: bool = False,
    ) -> Any:
        self.ultimo_filtro = filtro
        documento = next((doc for doc in self.documentos if self._coincide(doc, filtro)), None)
        if documento is None and upsert:
            documento = dict(filtro)
            self.documentos.append(documento)
        if documento is not None:
            documento.update(actualizacion["$set"])
        return SimpleNamespace()

    async def find_one(self, filtro: dict[str, Any]) -> dict[str, Any] | None:
        self.ultimo_filtro = filtro
        return next((doc for doc in self.documentos if self._coincide(doc, filtro)), None)

    async def delete_one(self, filtro: dict[str, Any]) -> Any:
        self.ultimo_filtro = filtro
        self.documentos[:] = [doc for doc in self.documentos if not self._coincide(doc, filtro)]
        return SimpleNamespace()

    @staticmethod
    def _coincide(documento: dict[str, Any], filtro: dict[str, Any]) -> bool:
        return all(documento.get(campo) == valor for campo, valor in filtro.items())


def _repo(
    documentos: list[dict[str, Any]] | None = None,
) -> tuple[CredencialesGraphMongo, _ColeccionFalsa]:
    coleccion = _ColeccionFalsa(documentos)
    config = Configuracion(
        mongodb_uri="mongodb://prueba",
        brujula_token_encryption_key=CLAVE,
    )
    return CredencialesGraphMongo(config, _coleccion=coleccion), coleccion


async def test_guardar_persiste_solo_el_refresh_token_cifrado() -> None:
    repo, coleccion = _repo()

    await repo.guardar_refresh_token(USUARIO, TOKEN, AHORA)

    documento = coleccion.documentos[0]
    assert documento["usuario_id"] == USUARIO
    assert documento["actualizado_en"] == AHORA
    assert documento["refresh_token_cifrado"] != TOKEN
    assert TOKEN not in documento["refresh_token_cifrado"]
    assert "refresh_token" not in documento


async def test_obtener_descifra_el_token_del_usuario_solicitado() -> None:
    cifrador = CifradorTokens(CLAVE)
    repo, _ = _repo([{"usuario_id": USUARIO, "refresh_token_cifrado": cifrador.cifrar(TOKEN)}])

    token = await repo.obtener_refresh_token(USUARIO)

    assert token == TOKEN


async def test_obtener_credenciales_ajenas_no_devuelve_token() -> None:
    cifrador = CifradorTokens(CLAVE)
    repo, coleccion = _repo(
        [{"usuario_id": OTRO_USUARIO, "refresh_token_cifrado": cifrador.cifrar(TOKEN)}]
    )

    token = await repo.obtener_refresh_token(USUARIO)

    assert token is None
    assert coleccion.ultimo_filtro == {"usuario_id": USUARIO}


async def test_borrar_elimina_solo_las_credenciales_del_usuario() -> None:
    cifrador = CifradorTokens(CLAVE)
    repo, coleccion = _repo(
        [
            {"usuario_id": USUARIO, "refresh_token_cifrado": cifrador.cifrar(TOKEN)},
            {"usuario_id": OTRO_USUARIO, "refresh_token_cifrado": cifrador.cifrar(TOKEN)},
        ]
    )

    await repo.borrar_credenciales(USUARIO)

    assert coleccion.ultimo_filtro == {"usuario_id": USUARIO}
    assert [documento["usuario_id"] for documento in coleccion.documentos] == [OTRO_USUARIO]
