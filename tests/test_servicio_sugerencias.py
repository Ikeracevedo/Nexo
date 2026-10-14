"""ServicioSugerencias se prueba sin Mongo mediante un doble de puerto."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.dominio.pendiente import FuentePendiente, Pendiente
from app.dominio.sugerencia import DeQuien, EstadoSugerencia, Sugerencia
from app.servicios.servicio_sugerencias import ServicioSugerencias

USUARIO = "usuario-aad"
AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


class _RepositorioFalso:
    def __init__(
        self,
        pendientes: list[Sugerencia] | None = None,
        sugerencia: Sugerencia | None = None,
        cambio: bool = True,
    ) -> None:
        self.pendientes = pendientes or []
        self.sugerencia = sugerencia
        self.cambio = cambio
        self.guardados: tuple[str, list[Sugerencia], datetime] | None = None
        self.ultimo_estado: tuple[str, str, EstadoSugerencia] | None = None

    async def guardar_nuevas(
        self,
        usuario_id: str,
        sugerencias: list[Sugerencia],
        detectadas_en: datetime,
    ) -> None:
        self.guardados = (usuario_id, sugerencias, detectadas_en)

    async def listar_pendientes(self, usuario_id: str) -> list[Sugerencia]:
        return self.pendientes

    async def obtener(self, sugerencia_id: str, usuario_id: str) -> Sugerencia | None:
        return self.sugerencia

    async def cambiar_estado(
        self,
        sugerencia_id: str,
        usuario_id: str,
        estado: EstadoSugerencia,
    ) -> bool:
        self.ultimo_estado = (sugerencia_id, usuario_id, estado)
        return self.cambio


class _PendientesFalsos:
    def __init__(self) -> None:
        self.guardados: tuple[str, str, datetime | None] | None = None
        self.borrados: list[tuple[str, str]] = []

    async def guardar(self, usuario_id: str, titulo: str, vence: datetime | None) -> Pendiente:
        self.guardados = (usuario_id, titulo, vence)
        return Pendiente(
            id="propio-1",
            titulo=titulo,
            fuente=FuentePendiente.PROPIO,
            url_origen="https://teams.microsoft.com",
            vence=vence,
        )

    async def borrar(self, pendiente_id: str, usuario_id: str) -> bool:
        self.borrados.append((pendiente_id, usuario_id))
        return True

    async def completar(self, pendiente_id: str, usuario_id: str) -> bool:
        return True


def _servicio(
    repositorio: _RepositorioFalso,
    pendientes: _PendientesFalsos | None = None,
) -> ServicioSugerencias:
    return ServicioSugerencias(repositorio, pendientes or _PendientesFalsos())


def _sugerencia() -> Sugerencia:
    return Sugerencia(
        id="sugerencia-1",
        texto="Enviar el informe",
        confianza=0.9,
        id_mensaje="mensaje-1",
        url_mensaje="https://teams.microsoft.com/l/message/chat/mensaje-1",
        conversacion="Proyecto TIC",
        de_quien=DeQuien.USUARIO,
        fecha=date(2026, 10, 15),
    )


@pytest.mark.asyncio
async def test_guarda_las_sugerencias_detectadas_para_el_usuario() -> None:
    repositorio = _RepositorioFalso()
    sugerencias = [_sugerencia()]

    await _servicio(repositorio).guardar_detectadas(USUARIO, sugerencias, AHORA)

    assert repositorio.guardados == (USUARIO, sugerencias, AHORA)


@pytest.mark.asyncio
async def test_lista_la_bandeja_pendiente() -> None:
    sugerencia = _sugerencia()
    servicio = _servicio(_RepositorioFalso([sugerencia]))

    assert await servicio.pendientes(USUARIO) == [sugerencia]


@pytest.mark.asyncio
async def test_descartar_envia_el_estado_correcto_y_devuelve_el_resultado() -> None:
    repositorio = _RepositorioFalso(cambio=True)

    descartada = await _servicio(repositorio).descartar("sugerencia-1", USUARIO)

    assert descartada is True
    assert repositorio.ultimo_estado == (
        "sugerencia-1",
        USUARIO,
        EstadoSugerencia.DESCARTADA,
    )


@pytest.mark.asyncio
async def test_descartar_ajena_devuelve_false() -> None:
    repositorio = _RepositorioFalso(cambio=False)

    descartada = await _servicio(repositorio).descartar("ajena", USUARIO)

    assert descartada is False


@pytest.mark.asyncio
async def test_aceptar_crea_un_pendiente_y_marca_la_sugerencia() -> None:
    sugerencia = _sugerencia()
    repositorio = _RepositorioFalso(sugerencia=sugerencia)
    pendientes = _PendientesFalsos()

    pendiente = await _servicio(repositorio, pendientes).aceptar("sugerencia-1", USUARIO)

    assert pendiente is not None
    assert pendientes.guardados == (
        USUARIO,
        "Enviar el informe",
        datetime(2026, 10, 15, tzinfo=UTC),
    )
    assert repositorio.ultimo_estado == (
        "sugerencia-1",
        USUARIO,
        EstadoSugerencia.ACEPTADA,
    )


@pytest.mark.asyncio
async def test_aceptar_inexistente_no_crea_un_pendiente() -> None:
    pendientes = _PendientesFalsos()

    pendiente = await _servicio(_RepositorioFalso(), pendientes).aceptar("no-existe", USUARIO)

    assert pendiente is None
    assert pendientes.guardados is None


@pytest.mark.asyncio
async def test_aceptar_reversa_el_pendiente_si_no_puede_cambiar_el_estado() -> None:
    pendientes = _PendientesFalsos()
    repositorio = _RepositorioFalso(sugerencia=_sugerencia(), cambio=False)

    pendiente = await _servicio(repositorio, pendientes).aceptar("sugerencia-1", USUARIO)

    assert pendiente is None
    assert pendientes.borrados == [("propio-1", USUARIO)]
