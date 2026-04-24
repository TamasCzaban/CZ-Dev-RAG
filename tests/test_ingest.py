"""Unit tests for scripts/ingest.py — no real HTTP calls."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.ingest import _collect_files, ingest_folder

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_docs(tmp_path: Path) -> tuple[Path, Path]:
    """Create two synthetic markdown files and return their paths."""
    doc_a = tmp_path / "doc_a.md"
    doc_b = tmp_path / "doc_b.md"
    doc_a.write_text("# Doc A\n\nContent of document A.", encoding="utf-8")
    doc_b.write_text("# Doc B\n\nContent of document B.", encoding="utf-8")
    return doc_a, doc_b


# ---------------------------------------------------------------------------
# _collect_files
# ---------------------------------------------------------------------------


def test_collect_files_non_recursive(tmp_path: Path) -> None:
    doc_a, doc_b = _make_docs(tmp_path)
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "doc_c.md").write_text("C", encoding="utf-8")

    files = _collect_files(tmp_path, recursive=False)
    assert set(files) == {doc_a, doc_b}


def test_collect_files_recursive(tmp_path: Path) -> None:
    doc_a, doc_b = _make_docs(tmp_path)
    subdir = tmp_path / "sub"
    subdir.mkdir()
    doc_c = subdir / "doc_c.md"
    doc_c.write_text("C", encoding="utf-8")

    files = _collect_files(tmp_path, recursive=True)
    assert set(files) == {doc_a, doc_b, doc_c}


def test_collect_files_filters_extensions(tmp_path: Path) -> None:
    (tmp_path / "keep.md").write_text("keep", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")
    (tmp_path / "skip.json").write_text("{}", encoding="utf-8")
    (tmp_path / "skip.py").write_text("", encoding="utf-8")

    files = _collect_files(tmp_path, recursive=False)
    names = {f.name for f in files}
    assert names == {"keep.md", "keep.txt"}


# ---------------------------------------------------------------------------
# ingest_folder — dry run
# ---------------------------------------------------------------------------


def test_dry_run_makes_no_http_calls(tmp_path: Path) -> None:
    _make_docs(tmp_path)

    with patch("scripts.ingest.httpx.Client") as mock_client_cls:
        exit_code = ingest_folder(
            tmp_path,
            recursive=True,
            dry_run=True,
            lightrag_url="http://localhost:9621",
        )

    mock_client_cls.assert_not_called()
    assert exit_code == 0


# ---------------------------------------------------------------------------
# ingest_folder — real run (mocked HTTP)
# ---------------------------------------------------------------------------


def test_ingest_posts_each_file(tmp_path: Path) -> None:
    _make_docs(tmp_path)

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("scripts.ingest.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.post.return_value = mock_response

        exit_code = ingest_folder(
            tmp_path,
            recursive=True,
            dry_run=False,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 0
    assert mock_instance.post.call_count == 2


def test_ingest_posts_correct_url_and_body(tmp_path: Path) -> None:
    single_dir = tmp_path / "single"
    single_dir.mkdir()
    test_file = single_dir / "test.md"
    test_file.write_text("Hello world", encoding="utf-8")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("scripts.ingest.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.post.return_value = mock_response

        exit_code = ingest_folder(
            single_dir,
            recursive=False,
            dry_run=False,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 0
    assert mock_instance.post.call_count == 1

    call_args = mock_instance.post.call_args
    assert call_args[0][0] == "http://localhost:9621/documents/text"

    payload = call_args[1]["json"]
    assert payload["text"] == "Hello world"
    assert payload["metadata"]["source"] == "test.md"
    assert payload["metadata"]["filename"] == "test.md"


def test_ingest_returns_nonzero_on_failure(tmp_path: Path) -> None:
    _make_docs(tmp_path)

    import httpx as _httpx

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    http_error = _httpx.HTTPStatusError(
        "500",
        request=MagicMock(),
        response=mock_response,
    )

    with patch("scripts.ingest.httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_instance.post.side_effect = http_error

        exit_code = ingest_folder(
            tmp_path,
            recursive=True,
            dry_run=False,
            lightrag_url="http://localhost:9621",
        )

    assert exit_code == 1


def test_ingest_empty_folder_returns_zero(tmp_path: Path) -> None:
    exit_code = ingest_folder(
        tmp_path,
        recursive=True,
        dry_run=False,
        lightrag_url="http://localhost:9621",
    )
    assert exit_code == 0


def test_ingest_nonexistent_folder_returns_nonzero(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    exit_code = ingest_folder(
        missing,
        recursive=True,
        dry_run=False,
        lightrag_url="http://localhost:9621",
    )
    assert exit_code == 1
