"""La caché de precarga persiste metadatos, nunca conversaciones."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.adaptadores.estado_precarga_mongo import EstadoPrecargaMongo
from app.config import Configuracion
from app.dominio.precarga import EstadoPrecarga

USUARIO = "usuario-aad"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _ColeccionFalsa:
    def __init__(self) -> None:
        self.documento: dict[str, Any] | None = None
        self.actualizacion: dict[str, Any] | None = None

    async def find_one(self, filtro: dict[str, Any]) -> dict[str, Any] | None:
        return self.documento if filtro == {"usuario_id": USUARIO} else None

    async def update_one(
        self, filtro: dict[str, Any], actualizacion: dict[str, Any], upsert: bool
    ) -> None:
        self.actualizacion = actualizacion
        self.documento = {**filtro, **actualizacion["$set"]}


async def test_guardar_conserva_solo_huella_y_fecha() -> None:
    coleccion = _ColeccionFalsa()
    repo = EstadoPrecargaMongo(Configuracion(mongodb_uri="mongodb://prueba"), _coleccion=coleccion)

    await repo.guardar(USUARIO, EstadoPrecarga(AHORA, "huella"))

    assert coleccion.documento == {
        "usuario_id": USUARIO,
        "ultima_precarga_en": AHORA,
        "huella_mensajes": "huella",
    }
    assert "texto" not in coleccion.documento


async def test_obtener_reconstruye_el_estado_del_usuario() -> None:
    coleccion = _ColeccionFalsa()
    coleccion.documento = {
        "usuario_id": USUARIO,
        "ultima_precarga_en": AHORA,
        "huella_mensajes": "huella",
    }
    repo = EstadoPrecargaMongo(Configuracion(mongodb_uri="mongodb://prueba"), _coleccion=coleccion)

    assert await repo.obtener(USUARIO) == EstadoPrecarga(AHORA, "huella")


async def test_obtener_asigna_utc_al_estado_historico_sin_zona_horaria() -> None:
    coleccion = _ColeccionFalsa()
    coleccion.documento = {
        "usuario_id": USUARIO,
        "ultima_precarga_en": AHORA.replace(tzinfo=None),
        "huella_mensajes": "huella",
    }
    repo = EstadoPrecargaMongo(Configuracion(mongodb_uri="mongodb://prueba"), _coleccion=coleccion)

    assert await repo.obtener(USUARIO) == EstadoPrecarga(AHORA, "huella")
