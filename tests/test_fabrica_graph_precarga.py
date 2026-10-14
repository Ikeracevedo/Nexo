"""La credencial de precarga conserva el access token solo en memoria."""

from __future__ import annotations

from app.adaptadores.fabrica_graph_precarga import _CredencialTokenFijo


async def test_credencial_entrega_el_access_token_renovado() -> None:
    credencial = _CredencialTokenFijo("access-token-efimero")

    token = await credencial.get_token("https://graph.microsoft.com/.default")

    assert token.token == "access-token-efimero"
    assert token.expires_on > 0
