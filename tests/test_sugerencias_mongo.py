"""SugerenciasMongo se prueba sin Mongo real y con aislamiento por usuario."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

from bson import ObjectId

from app.adaptadores.sugerencias_mongo import SugerenciasMongo
from app.config import Configuracion
from app.dominio.sugerencia import DeQuien, EstadoSugerencia, Sugerencia

USUARIO = "usuario-aad"
OTRO_USUARIO = "otro-aad"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _CursorFalso:
    def __init__(self, documentos: list[dict[str, Any]]) -> None:
        self._documentos = documentos

    async def to_list(self) -> list[dict[str, Any]]:
        return self._documentos


class _ColeccionFalsa:
    def __init__(self, documentos: list[dict[str, Any]] | None = None) -> None:
        self.documentos = documentos or []
        self.ultimo_filtro: dict[str, Any] | None = None
        self.ultima_actualizacion: dict[str, Any] | None = None

    async def update_one(
        self,
        filtro: dict[str, Any],
        actualizacion: dict[str, Any],
        upsert: bool = False,
    ) -> Any:
        self.ultimo_filtro = filtro
        self.ultima_actualizacion = actualizacion
        documento = next((doc for doc in self.documentos if self._coincide(doc, filtro)), None)

        if documento is None and upsert:
            documento = {**filtro, **actualizacion.get("$setOnInsert", {}), "_id": ObjectId()}
            self.documentos.append(documento)
            return SimpleNamespace(matched_count=0)

        if documento is not None:
            documento.update(actualizacion.get("$set", {}))
            return SimpleNamespace(matched_count=1)

        return SimpleNamespace(matched_count=0)

    def find(self, filtro: dict[str, Any]) -> _CursorFalso:
        self.ultimo_filtro = filtro
        return _CursorFalso([doc for doc in self.documentos if self._coincide(doc, filtro)])

    async def find_one(self, filtro: dict[str, Any]) -> dict[str, Any] | None:
        self.ultimo_filtro = filtro
        return next((doc for doc in self.documentos if self._coincide(doc, filtro)), None)

    @staticmethod
    def _coincide(documento: dict[str, Any], filtro: dict[str, Any]) -> bool:
        return all(documento.get(campo) == valor for campo, valor in filtro.items())


def _sugerencia() -> Sugerencia:
    return Sugerencia(
        texto="Enviar el informe",
        confianza=0.9,
        id_mensaje="mensaje-1",
        url_mensaje="https://teams.microsoft.com/l/message/chat/mensaje-1",
        conversacion="Proyecto TIC",
        de_quien=DeQuien.USUARIO,
        fecha=date(2026, 10, 15),
    )


def _repo(
    documentos: list[dict[str, Any]] | None = None,
) -> tuple[SugerenciasMongo, _ColeccionFalsa]:
    coleccion = _ColeccionFalsa(documentos)
    repo = SugerenciasMongo(Configuracion(mongodb_uri="mongodb://prueba"), _coleccion=coleccion)
    return repo, coleccion


async def test_guardar_no_persiste_el_cuerpo_original_del_mensaje() -> None:
    repo, coleccion = _repo()

    await repo.guardar_nuevas(USUARIO, [_sugerencia()], AHORA)

    documento = coleccion.documentos[0]
    assert documento["usuario_id"] == USUARIO
    assert documento["texto"] == "Enviar el informe"
    assert documento["fecha"] == datetime(2026, 10, 15, tzinfo=UTC)
    assert "cuerpo_mensaje" not in documento
    assert "texto_original" not in documento


async def test_listar_pendientes_filtra_por_usuario_y_estado() -> None:
    propia = SugerenciasMongo._a_documento(_sugerencia(), USUARIO, AHORA) | {"_id": ObjectId()}
    ajena = SugerenciasMongo._a_documento(_sugerencia(), OTRO_USUARIO, AHORA) | {"_id": ObjectId()}
    aceptada = propia | {"_id": ObjectId(), "estado": EstadoSugerencia.ACEPTADA}
    repo, coleccion = _repo([propia, ajena, aceptada])

    sugerencias = await repo.listar_pendientes(USUARIO)

    assert [sugerencia.id for sugerencia in sugerencias] == [str(propia["_id"])]
    assert coleccion.ultimo_filtro == {
        "usuario_id": USUARIO,
        "estado": EstadoSugerencia.PENDIENTE,
    }


async def test_cambiar_estado_ajeno_falla_sin_modificarlo() -> None:
    documento = SugerenciasMongo._a_documento(_sugerencia(), OTRO_USUARIO, AHORA) | {
        "_id": ObjectId()
    }
    repo, coleccion = _repo([documento])

    cambio = await repo.cambiar_estado(
        str(documento["_id"]),
        USUARIO,
        EstadoSugerencia.DESCARTADA,
    )

    assert cambio is False
    assert documento["estado"] is EstadoSugerencia.PENDIENTE
    assert coleccion.ultimo_filtro == {
        "_id": documento["_id"],
        "usuario_id": USUARIO,
        "estado": EstadoSugerencia.PENDIENTE,
    }


async def test_descartada_no_vuelve_a_crearse_en_una_precarga_posterior() -> None:
    descartada = SugerenciasMongo._a_documento(_sugerencia(), USUARIO, AHORA) | {
        "_id": ObjectId(),
        "estado": EstadoSugerencia.DESCARTADA,
    }
    repo, coleccion = _repo([descartada])

    await repo.guardar_nuevas(USUARIO, [_sugerencia()], AHORA)

    assert len(coleccion.documentos) == 1
    assert coleccion.documentos[0]["estado"] is EstadoSugerencia.DESCARTADA


async def test_obtener_no_devuelve_sugerencia_ajena() -> None:
    documento = SugerenciasMongo._a_documento(_sugerencia(), OTRO_USUARIO, AHORA) | {
        "_id": ObjectId()
    }
    repo, _ = _repo([documento])

    sugerencia = await repo.obtener(str(documento["_id"]), USUARIO)

    assert sugerencia is None
