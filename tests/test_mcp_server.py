"""Unit tests for the MCP server — all LightRAG HTTP calls are mocked."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

# Patch the LightRAGClient before importing server so the module-level
# Server object is created with the mock in place.
from src.mcp_server import server as server_module
from src.mcp_server.lightrag_client import LightRAGClient

QUERY_FIXTURE: dict[str, Any] = {
    "response": "AcmeCo payment terms are net-30.",
    "sources": ["acmeco-msa.md"],
}

DOCS_FIXTURE: list[dict[str, Any]] = [
    {
        "id": "doc-001",
        "file_path": "examples/demo-corpus/acmeco-msa.md",
        "created_at": "2024-01-01T00:00:00Z",
        "chunk_count": 12,
    }
]


def _make_mock_client(query_return: Any = None, docs_return: Any = None) -> MagicMock:
    mock = MagicMock(spec=LightRAGClient)
    mock.query.return_value = query_return or QUERY_FIXTURE
    mock.list_documents.return_value = docs_return or DOCS_FIXTURE
    return mock


@pytest.mark.asyncio
async def test_query_kb_returns_correct_shape() -> None:
    mock_client = _make_mock_client()
    with patch.object(server_module, "LightRAGClient", return_value=mock_client):
        results = await server_module.call_tool(
            "query_kb", {"question": "payment terms", "mode": "hybrid"}
        )

    assert len(results) == 1
    data = json.loads(results[0].text)
    assert data["answer"] == "AcmeCo payment terms are net-30."
    assert data["sources"] == ["acmeco-msa.md"]
    assert isinstance(data["latency_ms"], int)


@pytest.mark.asyncio
async def test_query_kb_default_mode() -> None:
    mock_client = _make_mock_client()
    with patch.object(server_module, "LightRAGClient", return_value=mock_client):
        results = await server_module.call_tool("query_kb", {"question": "anything"})

    mock_client.query.assert_called_once_with("anything", "hybrid")
    data = json.loads(results[0].text)
    assert "answer" in data


@pytest.mark.asyncio
async def test_list_documents_returns_correct_shape() -> None:
    mock_client = _make_mock_client()
    with patch.object(server_module, "LightRAGClient", return_value=mock_client):
        results = await server_module.call_tool("list_documents", {})

    assert len(results) == 1
    docs = json.loads(results[0].text)
    assert isinstance(docs, list)
    assert len(docs) == 1
    doc = docs[0]
    assert doc["doc_id"] == "doc-001"
    assert "source_path" in doc
    assert "ingested_at" in doc
    assert "chunk_count" in doc


@pytest.mark.asyncio
async def test_invalid_mode_returns_structured_error() -> None:
    mock_client = _make_mock_client()
    with patch.object(server_module, "LightRAGClient", return_value=mock_client):
        results = await server_module.call_tool("query_kb", {"question": "Q", "mode": "turbo"})

    data = json.loads(results[0].text)
    assert "error" in data
    assert "turbo" in data["error"]
    # Client should NOT have been called
    mock_client.query.assert_not_called()


@pytest.mark.asyncio
async def test_network_failure_returns_structured_error() -> None:
    mock_client = _make_mock_client()
    mock_client.query.side_effect = httpx.ConnectError("connection refused")
    with patch.object(server_module, "LightRAGClient", return_value=mock_client):
        results = await server_module.call_tool("query_kb", {"question": "Q", "mode": "hybrid"})

    data = json.loads(results[0].text)
    assert "error" in data
    assert "Cannot reach LightRAG" in data["error"]
