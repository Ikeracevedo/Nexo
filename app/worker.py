"""Proceso de precarga separado del bot para mantener Teams responsivo."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from app.composicion import servicio_precarga
from app.config import obtener_configuracion

logger = logging.getLogger(__name__)
_INTERVALO_SONDEO_SEGUNDOS = 60


async def ejecutar_una_vez() -> int:
    """Ejecuta una pasada; el servicio decide qué usuarios ya están al día."""
    config = obtener_configuracion()
    return await servicio_precarga(config).actualizar_todos(datetime.now(UTC))


async def main() -> None:
    """Mantiene una pasada por minuto; cada usuario se limita a 30 minutos."""
    while True:
        try:
            actualizados = await ejecutar_una_vez()
            logger.info("Precarga terminada: %s usuario(s) actualizado(s)", actualizados)
        except Exception:
            logger.exception("Falló una pasada global de precarga")
        await asyncio.sleep(_INTERVALO_SONDEO_SEGUNDOS)


if __name__ == "__main__":
    asyncio.run(main())
