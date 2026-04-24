"""HTTP client for the BGE-reranker-v2-m3 infinity-emb service.

Infinity-emb exposes a POST /rerank endpoint that accepts:
    {"query": "...", "docs": ["...", "..."]}

and returns:
    {"results": [{"index": 0, "relevance_score": 0.95, "document": "..."}, ...]}

Results are already ordered by the service, but we sort explicitly to guarantee
descending relevance_score order regardless of server implementation.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

RERANK_HOST = os.environ.get("RERANK_HOST", "http://reranker:7997")
_RERANK_ENDPOINT = "/rerank"


class RerankClient:
    """Synchronous reranker client backed by the infinity-emb service."""

    def __init__(self, host: str = RERANK_HOST, timeout: float = 30.0) -> None:
        self._host = host.rstrip("/")
        self._timeout = timeout

    def rerank(
        self,
        query: str,
        chunks: list[str],
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Rerank *chunks* against *query* and return the top *top_n* results.

        Each returned dict has the shape:
            {"index": int, "relevance_score": float, "document": str}

        Results are sorted by relevance_score descending.

        Args:
            query: The search query string.
            chunks: Candidate text passages to score.
            top_n: Maximum number of results to return.

        Returns:
            List of at most *top_n* result dicts, sorted by relevance_score desc.

        Raises:
            httpx.HTTPStatusError: If the reranker service returns a non-2xx status.
            httpx.RequestError: If the reranker service is unreachable.
        """
        if not chunks:
            return []

        url = f"{self._host}{_RERANK_ENDPOINT}"
        payload: dict[str, Any] = {
            "query": query,
            "docs": chunks,
            "top_n": top_n,
        }

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

        data: dict[str, Any] = response.json()
        results: list[dict[str, Any]] = list(data.get("results", []))

        # Sort by relevance_score descending -- guarantees order even if the
        # server returns results in a different order.
        results.sort(key=lambda r: float(r.get("relevance_score", 0.0)), reverse=True)

        return results[:top_n]
