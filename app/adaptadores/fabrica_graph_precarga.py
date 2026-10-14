"""Construye clientes Graph efímeros para el worker con tokens renovados."""

from __future__ import annotations

from time import time
from typing import Any

from azure.core.credentials import AccessToken
from msgraph import GraphServiceClient

from app.adaptadores.graph_chats import FuenteChatsGraph

_SCOPES_GRAPH = ["https://graph.microsoft.com/.default"]
_VIDA_TOKEN_SEGUNDOS = 300


class _CredencialTokenFijo:
    """Adaptador mínimo para que el SDK use un access token ya renovado."""

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token

    async def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        return AccessToken(self._access_token, int(time()) + _VIDA_TOKEN_SEGUNDOS)


class FabricaFuenteChatsGraph:
    """Crea una fuente nueva por usuario y ejecución; nunca cachea su token."""

    def __init__(self, bot_id: str) -> None:
        self._bot_id = bot_id

    def crear(self, usuario_id: str, access_token: str) -> FuenteChatsGraph:
        cliente = GraphServiceClient(
            credentials=_CredencialTokenFijo(access_token),
            scopes=_SCOPES_GRAPH,
        )
        return FuenteChatsGraph(cliente, usuario_id, self._bot_id)
