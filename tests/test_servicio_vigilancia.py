"""El consentimiento de vigilancia se prueba sin Teams ni MongoDB."""

from __future__ import annotations

from datetime import UTC, datetime

from app.servicios.servicio_vigilancia import MENSAJE_VIGILANCIA_ACTIVADA, ServicioVigilancia

UID = "aad-user-00000000-0000-0000-0000-000000000001"
AHORA = datetime(2026, 10, 14, 10, 0, tzinfo=UTC)


class _PreferenciasFalsas:
    def __init__(self, activa: bool = False) -> None:
        self.activa = activa
        self.activaciones: list[tuple[str, datetime]] = []
        self.desactivaciones: list[str] = []

    async def vigilancia_activa(self, usuario_id: str) -> bool:
        return self.activa

    async def activar_vigilancia(self, usuario_id: str, activada_en: datetime) -> None:
        self.activaciones.append((usuario_id, activada_en))
        self.activa = True

    async def desactivar_vigilancia(self, usuario_id: str) -> None:
        self.desactivaciones.append(usuario_id)
        self.activa = False

    async def usuarios_con_vigilancia_activa(self) -> list[str]:
        return [UID] if self.activa else []


class _CredencialesFalsas:
    def __init__(self) -> None:
        self.eliminadas: list[str] = []

    async def guardar_refresh_token(
        self, usuario_id: str, refresh_token: str, actualizado_en: datetime
    ) -> None:
        pass

    async def obtener_refresh_token(self, usuario_id: str) -> str | None:
        return None

    async def borrar_credenciales(self, usuario_id: str) -> None:
        self.eliminadas.append(usuario_id)


async def test_vigilar_activa_expresamente_y_entrega_el_consentimiento_completo() -> None:
    repo = _PreferenciasFalsas()
    servicio = ServicioVigilancia(repo, _CredencialesFalsas())

    mensaje = await servicio.activar(UID, AHORA)

    assert repo.activaciones == [(UID, AHORA)]
    assert mensaje == MENSAJE_VIGILANCIA_ACTIVADA
    assert "últimos 7 días" in mensaje
    assert "No guardo el texto" in mensaje
    assert "no vigilar" in mensaje


async def test_no_vigilar_desactiva_la_preferencia_del_usuario() -> None:
    repo = _PreferenciasFalsas(activa=True)
    credenciales = _CredencialesFalsas()
    servicio = ServicioVigilancia(repo, credenciales)

    mensaje = await servicio.desactivar(UID)

    assert repo.desactivaciones == [UID]
    assert credenciales.eliminadas == [UID]
    assert repo.activa is False
    assert "desactivada" in mensaje


async def test_usuario_nuevo_tiene_vigilancia_apagada_por_defecto() -> None:
    servicio = ServicioVigilancia(_PreferenciasFalsas(), _CredencialesFalsas())

    assert await servicio.activa(UID) is False
