"""PreferenciasMongo se prueba sin Mongo real y con opt-in por defecto."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.adaptadores.preferencias_mongo import PreferenciasMongo
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError

UID = "aad-user-00000000-0000-0000-0000-000000000001"
AHORA = datetime(2026, 10, 14, 10, 0, tzinfo=UTC)


class _ColeccionFalsa:
    def __init__(self, documento: dict[str, Any] | None = None) -> None:
        self.documento = documento
        self.ultimo_filtro_lectura: dict[str, Any] | None = None
        self.ultimo_filtro_escritura: dict[str, Any] | None = None
        self.ultima_actualizacion: dict[str, Any] | None = None
        self.ultimo_upsert: bool = False

    def find(self, filtro: dict[str, Any], proyeccion: dict[str, int]) -> _CursorFalso:
        self.ultimo_filtro_lectura = filtro
        documentos = [self.documento] if self.documento else []
        return _CursorFalso(documentos)

    async def find_one(self, filtro: dict[str, Any]) -> dict[str, Any] | None:
        self.ultimo_filtro_lectura = filtro
        return self.documento

    async def update_one(
        self,
        filtro: dict[str, Any],
        actualizacion: dict[str, Any],
        upsert: bool = False,
    ) -> None:
        self.ultimo_filtro_escritura = filtro
        self.ultima_actualizacion = actualizacion
        self.ultimo_upsert = upsert


class _CursorFalso:
    def __init__(self, documentos: list[dict[str, Any]]) -> None:
        self._documentos = documentos

    async def to_list(self) -> list[dict[str, Any]]:
        return self._documentos


def _repo(
    documento: dict[str, Any] | None = None,
) -> tuple[PreferenciasMongo, _ColeccionFalsa]:
    coleccion = _ColeccionFalsa(documento)
    repo = PreferenciasMongo(Configuracion(mongodb_uri="mongodb://prueba"), _coleccion=coleccion)
    return repo, coleccion


async def test_sin_preferencia_la_vigilancia_esta_apagada() -> None:
    repo, coleccion = _repo()

    activa = await repo.vigilancia_activa(UID)

    assert activa is False
    assert coleccion.ultimo_filtro_lectura == {"usuario_id": UID}


async def test_activar_guarda_fecha_y_filtra_por_usuario() -> None:
    repo, coleccion = _repo()

    await repo.activar_vigilancia(UID, AHORA)

    assert coleccion.ultimo_filtro_escritura == {"usuario_id": UID}
    assert coleccion.ultima_actualizacion == {
        "$set": {
            "vigilancia_activa": True,
            "activada_en": AHORA,
        }
    }
    assert coleccion.ultimo_upsert is True


async def test_desactivar_escribe_false_y_filtra_por_usuario() -> None:
    repo, coleccion = _repo()

    await repo.desactivar_vigilancia(UID)

    assert coleccion.ultimo_filtro_escritura == {"usuario_id": UID}
    assert coleccion.ultima_actualizacion == {"$set": {"vigilancia_activa": False}}
    assert coleccion.ultimo_upsert is False


async def test_documento_activo_devuelve_true() -> None:
    repo, _ = _repo({"usuario_id": UID, "vigilancia_activa": True})

    assert await repo.vigilancia_activa(UID) is True


async def test_listar_vigilancia_activa_devuelve_solo_identificadores() -> None:
    repo, coleccion = _repo({"usuario_id": UID, "vigilancia_activa": True})

    usuarios = await repo.usuarios_con_vigilancia_activa()

    assert usuarios == [UID]
    assert coleccion.ultimo_filtro_lectura == {"vigilancia_activa": True}


async def test_sin_mongodb_no_se_activa_silenciosamente() -> None:
    repo = PreferenciasMongo(Configuracion(mongodb_uri=""))

    with pytest.raises(FuenteNoDisponibleError):
        await repo.activar_vigilancia(UID, AHORA)
