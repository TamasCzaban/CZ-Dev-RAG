"""Unit tests for scripts/delete_by_source.py — no real HTTP calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scripts.delete_by_source import delete_document

# ---------------------------------------------------------------------------
# --yes flag skips confirmation
# ---------------------------------------------------------------------------


def test_yes_flag_sends_delete_without_prompt() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("scripts.delete_by_source.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.delete.return_value = mock_response

        exit_code = delete_document(
            "doc-abc-123",
            yes=True,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 0
    mock_instance.delete.assert_called_once_with(
        "http://localhost:9621/documents/doc-abc-123",
        timeout=30.0,
    )


# ---------------------------------------------------------------------------
# Confirmation prompt — user says 'y'
# ---------------------------------------------------------------------------


def test_prompt_yes_sends_delete() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with (
        patch("scripts.delete_by_source.httpx.Client") as mock_client_cls,
        patch("scripts.delete_by_source.typer.prompt", return_value="y"),
    ):
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.delete.return_value = mock_response

        exit_code = delete_document(
            "doc-abc-123",
            yes=False,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 0
    mock_instance.delete.assert_called_once()


# ---------------------------------------------------------------------------
# Confirmation prompt — user says 'n'
# ---------------------------------------------------------------------------


def test_prompt_no_aborts_without_delete() -> None:
    with (
        patch("scripts.delete_by_source.httpx.Client") as mock_client_cls,
        patch("scripts.delete_by_source.typer.prompt", return_value="n"),
    ):
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        exit_code = delete_document(
            "doc-abc-123",
            yes=False,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 1
    mock_instance.delete.assert_not_called()


def test_prompt_empty_aborts_without_delete() -> None:
    with (
        patch("scripts.delete_by_source.httpx.Client") as mock_client_cls,
        patch("scripts.delete_by_source.typer.prompt", return_value=""),
    ):
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        exit_code = delete_document(
            "doc-abc-123",
            yes=False,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 1
    mock_instance.delete.assert_not_called()


# ---------------------------------------------------------------------------
# HTTP error handling
# ---------------------------------------------------------------------------


def test_http_error_returns_nonzero() -> None:
    import httpx as _httpx

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    http_error = _httpx.HTTPStatusError(
        "404",
        request=MagicMock(),
        response=mock_response,
    )

    with patch("scripts.delete_by_source.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.delete.side_effect = http_error

        exit_code = delete_document(
            "doc-missing",
            yes=True,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 1


def test_request_error_returns_nonzero() -> None:
    import httpx as _httpx

    with patch("scripts.delete_by_source.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.delete.side_effect = _httpx.ConnectError("Connection refused")

        exit_code = delete_document(
            "doc-abc-123",
            yes=True,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 1
