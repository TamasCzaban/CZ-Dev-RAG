"""Thin HTTP client wrapping the LightRAG REST API."""

from __future__ import annotations

from typing import Any

import httpx

# Qwen2.5-32B can take 2–3 min to synthesise an answer on a 3090.
_QUERY_TIMEOUT = 300.0
_DEFAULT_TIMEOUT = 30.0


class LightRAGClient:
    """Async client for the LightRAG server."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)

    async def query(self, question: str, mode: str = "hybrid") -> dict[str, Any]:
        """POST /query → {"query": question, "mode": mode} and return response JSON."""
        resp = await self._client.post(
            f"{self.base_url}/query",
            json={"query": question, "mode": mode},
            timeout=_QUERY_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    async def list_documents(self) -> list[dict[str, Any]]:
        """GET /documents → list of document metadata dicts."""
        resp = await self._client.get(f"{self.base_url}/documents")
        resp.raise_for_status()
        data = resp.json()
        # LightRAG may wrap list in {"documents": [...]}
        if isinstance(data, dict):
            return data.get("documents", [])  # type: ignore[no-any-return]
        return data  # type: ignore[no-any-return]

    async def close(self) -> None:
        await self._client.aclose()
