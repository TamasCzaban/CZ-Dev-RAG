"""Unit tests for src/rerank/client.py.

All tests mock httpx.Client.post -- no real HTTP calls are made.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from rerank.client import RerankClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

QUERY = "What are AcmeCo's revenue projections for Q3?"

CHUNKS: list[str] = [
    f"AcmeCo document chunk number {i:02d}. "
    "This is synthetic test content used only in unit tests."
    for i in range(20)
]

# The service returns 5 scored results (indices need not be contiguous).
# Scores are deliberately out of order to verify the client sorts them.
_RAW_RESULTS: list[dict[str, Any]] = [
    {"index": 7, "relevance_score": 0.62, "document": CHUNKS[7]},
    {"index": 3, "relevance_score": 0.91, "document": CHUNKS[3]},
    {"index": 14, "relevance_score": 0.75, "document": CHUNKS[14]},
    {"index": 0, "relevance_score": 0.88, "document": CHUNKS[0]},
    {"index": 11, "relevance_score": 0.43, "document": CHUNKS[11]},
]

_EXPECTED_ORDER: list[float] = [0.91, 0.88, 0.75, 0.62, 0.43]


def _make_mock_response(results: list[dict[str, Any]]) -> MagicMock:
    """Build a mock httpx.Response that returns *results* as JSON."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": results}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRerankClientRerank:
    """Tests for RerankClient.rerank()."""

    def test_returns_top_n_results(self) -> None:
        """Client returns exactly top_n results."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp):
            client = RerankClient(host="http://reranker:7997")
            results = client.rerank(QUERY, CHUNKS, top_n=5)

        assert len(results) == 5

    def test_results_sorted_by_score_descending(self) -> None:
        """Client sorts results by relevance_score descending, regardless of server order."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp):
            client = RerankClient(host="http://reranker:7997")
            results = client.rerank(QUERY, CHUNKS, top_n=5)

        scores = [float(r["relevance_score"]) for r in results]
        assert scores == _EXPECTED_ORDER, f"Expected {_EXPECTED_ORDER}, got {scores}"

    def test_top_n_truncates_when_fewer_requested(self) -> None:
        """Requesting top_n=3 returns at most 3 results."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp):
            client = RerankClient(host="http://reranker:7997")
            results = client.rerank(QUERY, CHUNKS, top_n=3)

        assert len(results) == 3
        # Still sorted
        scores = [float(r["relevance_score"]) for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_post_called_with_correct_url(self) -> None:
        """HTTP POST is sent to /rerank on the configured host."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            client = RerankClient(host="http://reranker:7997")
            client.rerank(QUERY, CHUNKS, top_n=5)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        url = call_args.args[0] if call_args.args else call_args.kwargs.get("url")
        assert url == "http://reranker:7997/rerank"

    def test_post_body_has_query_field(self) -> None:
        """Request body includes the query string."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            client = RerankClient(host="http://reranker:7997")
            client.rerank(QUERY, CHUNKS, top_n=5)

        payload: dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert "query" in payload
        assert payload["query"] == QUERY

    def test_post_body_has_docs_field(self) -> None:
        """Request body uses 'docs' key (infinity-emb API spec)."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            client = RerankClient(host="http://reranker:7997")
            client.rerank(QUERY, CHUNKS, top_n=5)

        payload: dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert "docs" in payload, "Must use 'docs' key per infinity-emb API spec"
        assert payload["docs"] == CHUNKS

    def test_post_body_has_top_n_field(self) -> None:
        """Request body includes top_n so the server can do early truncation."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            client = RerankClient(host="http://reranker:7997")
            client.rerank(QUERY, CHUNKS, top_n=5)

        payload: dict[str, Any] = mock_post.call_args.kwargs["json"]
        assert payload.get("top_n") == 5

    def test_result_dicts_have_expected_keys(self) -> None:
        """Each result dict exposes index, relevance_score, and document."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp):
            client = RerankClient(host="http://reranker:7997")
            results = client.rerank(QUERY, CHUNKS, top_n=5)

        for result in results:
            assert "index" in result
            assert "relevance_score" in result
            assert "document" in result

    def test_empty_chunks_returns_empty_list(self) -> None:
        """Passing an empty chunks list short-circuits without making an HTTP call."""
        with patch("httpx.Client.post") as mock_post:
            client = RerankClient(host="http://reranker:7997")
            results = client.rerank(QUERY, [], top_n=5)

        assert results == []
        mock_post.assert_not_called()

    def test_custom_host_is_used(self) -> None:
        """RerankClient respects a custom host passed to the constructor."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            client = RerankClient(host="http://custom-host:8080")
            client.rerank(QUERY, CHUNKS, top_n=5)

        url = (
            mock_post.call_args.args[0]
            if mock_post.call_args.args
            else mock_post.call_args.kwargs.get("url")
        )
        assert url == "http://custom-host:8080/rerank"

    def test_raise_for_status_is_called(self) -> None:
        """Client calls raise_for_status() so HTTP errors propagate."""
        mock_resp = _make_mock_response(_RAW_RESULTS)
        with patch("httpx.Client.post", return_value=mock_resp):
            client = RerankClient(host="http://reranker:7997")
            client.rerank(QUERY, CHUNKS, top_n=5)

        mock_resp.raise_for_status.assert_called_once()
