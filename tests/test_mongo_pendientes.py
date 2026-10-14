"""FuentePropiaMongo se prueba sin MongoDB real, sin red, sin URI.

El adaptador acepta _coleccion como kwarg solo-para-tests: permite inyectar
una coleccion falsa en vez de un cliente real. La produccion no pasa _coleccion
y el adaptador crea AsyncMongoClient de forma perezosa.

El test de aislamiento entre usuarios es OBLIGATORIO: un find sin filtro
de usuario_id viola OWASP A01. Se prueba que dos usuarios solo ven sus
propios pendientes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.adaptadores.mongo_pendientes import FuentePropiaMongo
from app.config import Configuracion
from app.dominio.errores import FuenteNoDisponibleError
from app.dominio.pendiente import FuentePendiente
from app.servicios.servicio_agenda import ServicioAgenda

AHORA = datetime(2026, 9, 29, 10, 0, tzinfo=UTC)
LUEGO = AHORA + timedelta(days=7)
UID_A = "aad-user-a-00000000-0000-0000-0000-000000000001"
UID_B = "aad-user-b-00000000-0000-0000-0000-000000000002"


# ---------------------------------------------------------------------------
# Fakes de coleccion MongoDB
# ---------------------------------------------------------------------------


class _InsertResult:
    def __init__(self) -> None:
        self.inserted_id = "507f1f77bcf86cd799439011"


class _UpdateResult:
    def __init__(self, matched_count: int) -> None:
        self.matched_count = matched_count


class _DeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class _FakeCursor:
    """El error viene de to_list(), no de find(): igual que pymongo real."""

    def __init__(self, docs: list[dict[str, Any]], error: Exception | None = None) -> None:
        self._docs = docs
        self._error = error

    async def to_list(self) -> list[dict[str, Any]]:
        if self._error:
            raise self._error
        return list(self._docs)


class _FakeColeccion:
    def __init__(
        self,
        docs: list[dict[str, Any]] | None = None,
        error_find: Exception | None = None,
        error_insert: Exception | None = None,
        matched_count: int = 1,
        deleted_count: int = 1,
    ) -> None:
        self._docs = docs or []
        self._error_find = error_find
        self._error_insert = error_insert
        self._matched_count = matched_count
        self._deleted_count = deleted_count
        self.ultimo_filtro: dict[str, Any] | None = None
        self.ultimo_doc: dict[str, Any] | None = None
        self.ultimo_filtro_update: dict[str, Any] | None = None
        self.ultima_actualizacion: dict[str, Any] | None = None
        self.ultimo_filtro_delete: dict[str, Any] | None = None

    def find(self, filtro: dict[str, Any]) -> _FakeCursor:
        self.ultimo_filtro = filtro
        docs = [
            doc
            for doc in self._docs
            if doc["usuario_id"] == filtro["usuario_id"]
            and doc["completado"] is filtro["completado"]
        ]
        return _FakeCursor(docs, self._error_find)

    async def insert_one(self, doc: dict[str, Any]) -> _InsertResult:
        if self._error_insert:
            raise self._error_insert
        self.ultimo_doc = doc
        return _InsertResult()

    async def update_one(
        self,
        filtro: dict[str, Any],
        actualizacion: dict[str, Any],
    ) -> _UpdateResult:
        self.ultimo_filtro_update = filtro
        self.ultima_actualizacion = actualizacion
        if self._matched_count:
            for doc in self._docs:
                if (
                    str(filtro["_id"]) == str(doc["_id"])
                    and filtro["usuario_id"] == doc["usuario_id"]
                ):
                    doc.update(actualizacion["$set"])
        return _UpdateResult(matched_count=self._matched_count)

    async def delete_one(self, filtro: dict[str, Any]) -> _DeleteResult:
        self.ultimo_filtro_delete = filtro
        return _DeleteResult(deleted_count=self._deleted_count)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config(uri: str = "mongodb://test", bot_id: str = "") -> Configuracion:
    return Configuracion(mongodb_uri=uri, teams_bot_id=bot_id)


def _fuente(
    docs: list[dict[str, Any]] | None = None,
    usuario_id: str = UID_A,
    error_find: Exception | None = None,
    error_insert: Exception | None = None,
    matched_count: int = 1,
    deleted_count: int = 1,
) -> tuple[FuentePropiaMongo, _FakeColeccion]:
    col = _FakeColeccion(
        docs,
        error_find,
        error_insert,
        matched_count,
        deleted_count,
    )
    fuente = FuentePropiaMongo(_config(), usuario_id, _coleccion=col)
    return fuente, col


def _doc(
    usuario_id: str = UID_A,
    titulo: str = "Tarea",
    vence: datetime | None = None,
    completado: bool = False,
) -> dict[str, Any]:
    return {
        "_id": "507f1f77bcf86cd799439011",
        "usuario_id": usuario_id,
        "titulo": titulo,
        "vence": vence,
        "completado": completado,
        "creado_en": AHORA,
    }


# ---------------------------------------------------------------------------
# AISLAMIENTO ENTRE USUARIOS (obligatorio — OWASP A01)
# ---------------------------------------------------------------------------


async def test_aislamiento_usuario_a_no_ve_pendientes_de_b() -> None:
    """Dos usuarios, dos pendientes. Cada uno ve solo el suyo."""
    docs_a = [_doc(usuario_id=UID_A, titulo="Tarea de A")]
    docs_b = [_doc(usuario_id=UID_B, titulo="Tarea de B")]

    fuente_a, col_a = _fuente(docs=docs_a, usuario_id=UID_A)
    fuente_b, col_b = _fuente(docs=docs_b, usuario_id=UID_B)

    pendientes_a = await fuente_a.obtener_pendientes(AHORA, LUEGO)
    pendientes_b = await fuente_b.obtener_pendientes(AHORA, LUEGO)

    # Cada fuente consulta con SU usuario_id en el filtro
    assert col_a.ultimo_filtro is not None
    assert col_a.ultimo_filtro["usuario_id"] == UID_A
    assert col_b.ultimo_filtro is not None
    assert col_b.ultimo_filtro["usuario_id"] == UID_B

    assert all(p.titulo == "Tarea de A" for p in pendientes_a)
    assert all(p.titulo == "Tarea de B" for p in pendientes_b)


# ---------------------------------------------------------------------------
# Camino feliz — lectura
# ---------------------------------------------------------------------------


async def test_traduce_documento_a_pendiente() -> None:
    fuente, _ = _fuente(docs=[_doc(titulo="Entregar informe")])
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert p.titulo == "Entregar informe"
    assert p.fuente is FuentePendiente.PROPIO
    assert p.id.startswith("propio-")
    assert p.confianza == 1.0


async def test_sin_pendientes_devuelve_lista_vacia() -> None:
    fuente, _ = _fuente(docs=[])
    assert await fuente.obtener_pendientes(AHORA, LUEGO) == []


async def test_los_completados_no_se_devuelven() -> None:
    docs = [
        _doc(titulo="Abierta", completado=False),
        _doc(titulo="Cerrada", completado=True),
    ]
    # La coleccion falsa devuelve todos; el filtro lo maneja Mongo real.
    # Aqui verificamos que el filtro enviado a Mongo incluye completado: False.
    fuente, col = _fuente(docs=docs)
    await fuente.obtener_pendientes(AHORA, LUEGO)
    assert col.ultimo_filtro is not None
    assert col.ultimo_filtro.get("completado") is False


async def test_sin_fecha_se_devuelve_siempre() -> None:
    fuente, _ = _fuente(docs=[_doc(vence=None)])
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert p.vence is None


async def test_url_origen_no_esta_vacia() -> None:
    fuente, _ = _fuente(docs=[_doc()])
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert p.url_origen.startswith("https://")


async def test_url_origen_incluye_bot_id_si_configurado() -> None:
    bot_id = "b81a25fb-0000-0000-0000-000000000001"
    col = _FakeColeccion(docs=[_doc()])
    config = Configuracion(mongodb_uri="mongodb://test", teams_bot_id=bot_id)
    fuente = FuentePropiaMongo(config, UID_A, _coleccion=col)
    [p] = await fuente.obtener_pendientes(AHORA, LUEGO)
    assert bot_id in p.url_origen


# ---------------------------------------------------------------------------
# Camino feliz — escritura
# ---------------------------------------------------------------------------


async def test_guardar_crea_pendiente_con_id_asignado() -> None:
    fuente, _ = _fuente()
    p = await fuente.guardar(UID_A, "Comprar leche", None)
    assert p.id.startswith("propio-")
    assert p.titulo == "Comprar leche"
    assert p.fuente is FuentePendiente.PROPIO
    assert p.vence is None


async def test_guardar_con_fecha_devuelve_fecha() -> None:
    vence = AHORA + timedelta(days=2)
    fuente, _ = _fuente()
    p = await fuente.guardar(UID_A, "Revisar PR", vence)
    assert p.vence == vence


async def test_completar_actualiza_solo_el_pendiente_del_usuario() -> None:
    fuente, col = _fuente()

    completado = await fuente.completar(
        "propio-507f1f77bcf86cd799439011",
        UID_A,
    )

    assert completado is True
    assert col.ultimo_filtro_update is not None
    assert col.ultimo_filtro_update["usuario_id"] == UID_A
    assert col.ultima_actualizacion == {"$set": {"completado": True}}


async def test_borrar_elimina_solo_el_pendiente_del_usuario() -> None:
    fuente, col = _fuente()

    borrado = await fuente.borrar(
        "propio-507f1f77bcf86cd799439011",
        UID_A,
    )

    assert borrado is True
    assert col.ultimo_filtro_delete is not None
    assert col.ultimo_filtro_delete["usuario_id"] == UID_A


async def test_completar_pendiente_ajeno_devuelve_false() -> None:
    fuente, _ = _fuente(matched_count=0)

    completado = await fuente.completar(
        "propio-507f1f77bcf86cd799439011",
        UID_A,
    )

    assert completado is False


async def test_borrar_pendiente_ajeno_devuelve_false() -> None:
    fuente, _ = _fuente(deleted_count=0)

    borrado = await fuente.borrar(
        "propio-507f1f77bcf86cd799439011",
        UID_A,
    )

    assert borrado is False


async def test_completar_pendiente_inexistente_devuelve_false() -> None:
    fuente, _ = _fuente(matched_count=0)

    completado = await fuente.completar(
        "propio-507f1f77bcf86cd799439011",
        UID_A,
    )

    assert completado is False


async def test_un_pendiente_completado_desaparece_de_semana() -> None:
    fuente, _ = _fuente(docs=[_doc()])
    servicio = ServicioAgenda([fuente])

    agenda_antes = await servicio.pendientes_de_la_semana(AHORA)
    completado = await fuente.completar("propio-507f1f77bcf86cd799439011", UID_A)
    agenda_despues = await servicio.pendientes_de_la_semana(AHORA)

    assert agenda_antes.total == 1
    assert completado is True
    assert agenda_despues.total == 0


# ---------------------------------------------------------------------------
# Sin MONGODB_URI no rompe el arranque
# ---------------------------------------------------------------------------


async def test_sin_uri_obtener_pendientes_lanza_fuente_no_disponible() -> None:
    config = Configuracion(mongodb_uri="")
    fuente = FuentePropiaMongo(config, UID_A)
    with pytest.raises(FuenteNoDisponibleError):
        await fuente.obtener_pendientes(AHORA, LUEGO)


async def test_sin_uri_guardar_lanza_fuente_no_disponible() -> None:
    config = Configuracion(mongodb_uri="")
    fuente = FuentePropiaMongo(config, UID_A)
    with pytest.raises(FuenteNoDisponibleError):
        await fuente.guardar(UID_A, "Tarea", None)


# ---------------------------------------------------------------------------
# Errores de Mongo se reportan, no se tragan
# ---------------------------------------------------------------------------


async def test_error_de_find_lanza_fuente_no_disponible() -> None:
    fuente, _ = _fuente(error_find=RuntimeError("timeout de Mongo"))
    with pytest.raises(FuenteNoDisponibleError):
        await fuente.obtener_pendientes(AHORA, LUEGO)


async def test_error_de_insert_lanza_fuente_no_disponible() -> None:
    fuente, _ = _fuente(error_insert=RuntimeError("write concern"))
    with pytest.raises(FuenteNoDisponibleError):
        await fuente.guardar(UID_A, "Tarea", None)
