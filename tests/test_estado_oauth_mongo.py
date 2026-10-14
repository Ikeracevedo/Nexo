"""Estados OAuth: opacos, vencibles y de un solo uso."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.adaptadores.estado_oauth_mongo import EstadoOAuthMongo
from app.config import Configuracion

USUARIO = "usuario-aad"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _ColeccionFalsa:
    def __init__(self) -> None:
        self.documentos: list[dict[str, Any]] = []
        self.ultimo_filtro: dict[str, Any] | None = None

    async def insert_one(self, documento: dict[str, Any]) -> None:
        self.documentos.append(documento)

    async def find_one_and_update(
        self,
        filtro: dict[str, Any],
        actualizacion: dict[str, Any],
        return_document: bool,
    ) -> dict[str, Any] | None:
        self.ultimo_filtro = filtro
        for documento in self.documentos:
            if self._coincide(documento, filtro):
                documento.update(actualizacion["$set"])
                return documento
        return None

    @staticmethod
    def _coincide(documento: dict[str, Any], filtro: dict[str, Any]) -> bool:
        for campo, valor in filtro.items():
            if isinstance(valor, dict) and "$gt" in valor:
                if documento[campo] <= valor["$gt"]:
                    return False
            elif documento.get(campo) != valor:
                return False
        return True


def _repo() -> tuple[EstadoOAuthMongo, _ColeccionFalsa]:
    coleccion = _ColeccionFalsa()
    repositorio = EstadoOAuthMongo(
        Configuracion(mongodb_uri="mongodb://prueba"),
        _coleccion=coleccion,
    )
    return repositorio, coleccion


async def test_consumir_marca_el_estado_y_devuelve_su_usuario() -> None:
    repo, coleccion = _repo()
    expira_en = AHORA + timedelta(minutes=10)

    await repo.crear("estado-seguro", USUARIO, expira_en)
    usuario = await repo.consumir("estado-seguro", AHORA)

    assert usuario == USUARIO
    assert coleccion.documentos[0]["usado"] is True
    assert coleccion.documentos[0]["consumido_en"] == AHORA


async def test_estado_consumido_no_puede_reutilizarse() -> None:
    repo, _ = _repo()
    await repo.crear("estado-seguro", USUARIO, AHORA + timedelta(minutes=10))

    await repo.consumir("estado-seguro", AHORA)

    assert await repo.consumir("estado-seguro", AHORA) is None


async def test_estado_vencido_no_puede_consumirse() -> None:
    repo, coleccion = _repo()
    await repo.crear("estado-vencido", USUARIO, AHORA - timedelta(seconds=1))

    assert await repo.consumir("estado-vencido", AHORA) is None
    assert coleccion.ultimo_filtro == {
        "estado": "estado-vencido",
        "usado": False,
        "expira_en": {"$gt": AHORA},
    }
