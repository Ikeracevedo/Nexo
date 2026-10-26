"""
Composition root del proyecto.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.rutas import VERSION, router
from app.bot.bot_teams import crear_bot_teams
from app.config import obtener_configuracion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def crear_app() -> FastAPI:
    config = obtener_configuracion()

    @contextlib.asynccontextmanager
    async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
        await app.state.bot_teams.initialize()
        yield

    nucleo = FastAPI(
        title=config.bot_nombre,
        version=VERSION,
        description=(
            "Unifica pendientes dispersos de Microsoft 365 y los devuelve con enlace a su origen."
        ),
        lifespan=ciclo_de_vida,
    )
    nucleo.mount("/static", StaticFiles(directory="app/static"), name="static")
    nucleo.include_router(router)
    nucleo.state.bot_teams = crear_bot_teams(nucleo, config)

    return nucleo


app = crear_app()
