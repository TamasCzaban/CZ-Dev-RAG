"""Thin HTTP client wrapping the LightRAG REST API."""

from __future__ import annotations

from typing import Any

import httpx


class LightRAGClient:
    """Synchronous client for the LightRAG server."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=120.0)

    def query(self, question: str, mode: str = "hybrid") -> dict[str, Any]:
        """POST /query → {"query": question, "mode": mode} and return response JSON."""
        resp = self._client.post(
            f"{self.base_url}/query",
            json={"query": question, "mode": mode},
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def list_documents(self) -> list[dict[str, Any]]:
        """GET /documents → list of document metadata dicts."""
        resp = self._client.get(f"{self.base_url}/documents")
        resp.raise_for_status()
        data = resp.json()
        # LightRAG may wrap list in {"documents": [...]}
        if isinstance(data, dict):
            return data.get("documents", [])  # type: ignore[no-any-return]
        return data  # type: ignore[no-any-return]

    def close(self) -> None:
        self._client.close()
