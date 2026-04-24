"""Smoke tests for evals/run_evals.py.

All LightRAG HTTP calls and Ragas evaluate() are mocked.
No real network or LLM is required.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# Make sure the repo root is on sys.path so we can import evals.*
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import evals.run_evals as run_evals  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_GOLD_SET: list[dict[str, Any]] = [
    {
        "id": "q01",
        "question": "What are the payment terms in the AcmeCo MSA?",
        "ground_truth": "Invoices are due net thirty days from invoice date.",
        "relevant_doc_ids": ["acmeco-msa"],
        "mini": True,
    },
    {
        "id": "q02",
        "question": "What is the total value of SOW-001?",
        "ground_truth": "The total fixed price is €48,000.",
        "relevant_doc_ids": ["acmeco-sow-001"],
        "mini": False,
    },
]

FIXTURE_LIGHTRAG_RESPONSE = {
    "response": "Payment is due net 30 days.",
    "contexts": ["Section 4.1 Payment terms..."],
}

FIXTURE_RAGAS_RESULT: dict[str, float] = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.90,
    "context_precision": 0.80,
}


def _make_fake_httpx_response(data: dict[str, Any]) -> MagicMock:
    """Build a mock httpx.Response that returns the given dict on .json()."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _make_fake_ragas_result(scores: dict[str, float]) -> MagicMock:
    """Build a mock Ragas result object.

    Supports both dict-style access (result[key]) and .get(key) so that
    run_ragas() can retrieve per-metric averages without crashing.
    """
    mock_result = MagicMock()
    mock_result.__getitem__ = lambda self, k: scores[k]
    mock_result.get = lambda k, default=None: scores.get(k, default)
    return mock_result


# ---------------------------------------------------------------------------
# Helpers patching internals
# ---------------------------------------------------------------------------


def _patch_gold_set(questions: list[dict[str, Any]]) -> Any:
    """Patch load_gold_set to return a fixed question list."""
    return patch.object(run_evals, "load_gold_set", return_value=questions)


def _patch_httpx_post(response_data: dict[str, Any]) -> Any:
    """Patch httpx.Client.post so no real HTTP calls are made."""
    return patch(
        "httpx.Client.post",
        return_value=_make_fake_httpx_response(response_data),
    )


def _patch_ragas(scores: dict[str, float]) -> Any:
    """Patch run_ragas to return a fixed scores dict without calling Ragas."""
    return patch.object(run_evals, "run_ragas", return_value=scores)


def _patch_build_ragas_dataset() -> Any:
    """Patch build_ragas_dataset so it never imports Ragas."""
    return patch.object(run_evals, "build_ragas_dataset", return_value=MagicMock())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadGoldSet:
    """Unit tests for load_gold_set (reads real gold_set.jsonl)."""

    def test_load_all(self) -> None:
        questions = run_evals.load_gold_set(mini=False)
        assert len(questions) == 20

    def test_load_mini(self) -> None:
        questions = run_evals.load_gold_set(mini=True)
        assert len(questions) == 3
        assert all(q["mini"] is True for q in questions)

    def test_all_have_required_fields(self) -> None:
        questions = run_evals.load_gold_set(mini=False)
        required = {"id", "question", "ground_truth", "relevant_doc_ids", "mini"}
        for q in questions:
            assert required.issubset(q.keys()), f"Question {q.get('id')} missing fields"


class TestQueryLightrag:
    """Unit tests for query_lightrag (HTTP mocked)."""

    def test_happy_path(self) -> None:
        with _patch_httpx_post(FIXTURE_LIGHTRAG_RESPONSE):
            import httpx

            with httpx.Client() as client:
                answer, contexts = run_evals.query_lightrag(
                    client, "http://localhost:9621", "test question", "hybrid"
                )
        assert answer == "Payment is due net 30 days."
        assert isinstance(contexts, list)
        assert len(contexts) >= 1

    def test_fallback_on_error(self) -> None:
        with patch("httpx.Client.post", side_effect=Exception("connection refused")):
            import httpx

            with httpx.Client() as client:
                answer, contexts = run_evals.query_lightrag(
                    client, "http://localhost:9621", "test question", "naive"
                )
        assert answer == ""
        assert contexts == ["no context available"]


class TestWriteResultsCsv:
    """Unit tests for write_results_csv."""

    def test_creates_file_with_correct_columns(self, tmp_path: Path) -> None:
        rows = [
            {
                "mode": "naive",
                "question_id": "q01",
                "faithfulness": 0.85,
                "answer_relevancy": 0.90,
                "context_precision": 0.80,
            }
        ]
        # Temporarily redirect RESULTS_DIR
        original_dir = run_evals.RESULTS_DIR
        run_evals.RESULTS_DIR = tmp_path
        try:
            csv_path = run_evals.write_results_csv(rows, "20260101T000000Z")
        finally:
            run_evals.RESULTS_DIR = original_dir

        assert csv_path.exists()
        with csv_path.open() as f:
            reader = csv.DictReader(f)
            written_rows = list(reader)
        assert len(written_rows) == 1
        assert written_rows[0]["mode"] == "naive"
        assert written_rows[0]["question_id"] == "q01"
        assert "faithfulness" in written_rows[0]


class TestUpdateReadme:
    """Unit tests for the README marker replacement."""

    def test_replaces_eval_block(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            "Before\n"
            "<!-- EVAL:START -->\nold content\n<!-- EVAL:END -->\n"
            "After\n",
            encoding="utf-8",
        )
        original_path = run_evals.README_PATH
        run_evals.README_PATH = readme
        try:
            mode_averages = {
                "naive": {"faithfulness": 0.8, "answer_relevancy": 0.9, "context_precision": 0.7},
                "hybrid": {
                    "faithfulness": 0.85,
                    "answer_relevancy": 0.92,
                    "context_precision": 0.75,
                },
            }
            run_evals.update_readme(mode_averages)
        finally:
            run_evals.README_PATH = original_path

        content = readme.read_text(encoding="utf-8")
        assert "<!-- EVAL:START -->" in content
        assert "<!-- EVAL:END -->" in content
        assert "old content" not in content
        assert "naive" in content
        assert "hybrid" in content
        assert "Before" in content
        assert "After" in content

    def test_no_crash_when_markers_missing(self, tmp_path: Path, capsys: Any) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("No markers here.\n", encoding="utf-8")
        original_path = run_evals.README_PATH
        run_evals.README_PATH = readme
        try:
            naive_scores = {"faithfulness": 0.8, "answer_relevancy": 0.9, "context_precision": 0.7}
            run_evals.update_readme({"naive": naive_scores})
        finally:
            run_evals.README_PATH = original_path
        # Should not raise — content unchanged
        assert readme.read_text() == "No markers here.\n"


class TestMainCliMini:
    """Integration smoke test for the CLI --mini flag with all dependencies mocked."""

    def test_mini_writes_csv_with_correct_row_count(self, tmp_path: Path) -> None:
        """--mini should produce 3 questions x 1 mode = 3 CSV rows."""
        mini_questions = [q for q in FIXTURE_GOLD_SET if q["mini"]]
        assert len(mini_questions) == 1  # fixture has 1 mini question

        original_results_dir = run_evals.RESULTS_DIR
        run_evals.RESULTS_DIR = tmp_path

        with (
            _patch_gold_set(mini_questions),
            _patch_httpx_post(FIXTURE_LIGHTRAG_RESPONSE),
            _patch_build_ragas_dataset(),
            _patch_ragas(FIXTURE_RAGAS_RESULT),
        ):
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(run_evals.app, ["--mini", "--modes", "naive"])

        run_evals.RESULTS_DIR = original_results_dir

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        with csv_files[0].open() as f:
            rows = list(csv.DictReader(f))
        # 1 mini question x 1 mode = 1 row
        assert len(rows) == 1

    def test_full_run_writes_csv_multiple_modes(self, tmp_path: Path) -> None:
        """Full run: 2 questions x 2 modes = 4 CSV rows."""
        original_results_dir = run_evals.RESULTS_DIR
        run_evals.RESULTS_DIR = tmp_path

        with (
            _patch_gold_set(FIXTURE_GOLD_SET),
            _patch_httpx_post(FIXTURE_LIGHTRAG_RESPONSE),
            _patch_build_ragas_dataset(),
            _patch_ragas(FIXTURE_RAGAS_RESULT),
        ):
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(run_evals.app, ["--modes", "naive,hybrid"])

        run_evals.RESULTS_DIR = original_results_dir

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1
        with csv_files[0].open() as f:
            rows = list(csv.DictReader(f))
        # 2 questions x 2 modes = 4 rows
        assert len(rows) == 4

    def test_output_readme_updates_markers(self, tmp_path: Path) -> None:
        """--output-readme should replace content between EVAL markers."""
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Test\n"
            "<!-- EVAL:START -->\nplaceholder\n<!-- EVAL:END -->\n"
            "## Footer\n",
            encoding="utf-8",
        )

        original_results_dir = run_evals.RESULTS_DIR
        original_readme_path = run_evals.README_PATH
        run_evals.RESULTS_DIR = tmp_path
        run_evals.README_PATH = readme

        with (
            _patch_gold_set([FIXTURE_GOLD_SET[0]]),
            _patch_httpx_post(FIXTURE_LIGHTRAG_RESPONSE),
            _patch_build_ragas_dataset(),
            _patch_ragas(FIXTURE_RAGAS_RESULT),
        ):
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                run_evals.app, ["--modes", "naive", "--output-readme"]
            )

        run_evals.RESULTS_DIR = original_results_dir
        run_evals.README_PATH = original_readme_path

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        content = readme.read_text(encoding="utf-8")
        assert "<!-- EVAL:START -->" in content
        assert "<!-- EVAL:END -->" in content
        assert "placeholder" not in content
        assert "naive" in content


class TestBuildMarkdownTable:
    """Unit tests for markdown table rendering."""

    def test_nan_displayed_as_dash(self) -> None:

        mode_averages = {
            "naive": {
                "faithfulness": float("nan"),
                "answer_relevancy": 0.9,
                "context_precision": float("nan"),
            }
        }
        table = run_evals.build_markdown_table(mode_averages)
        assert "—" in table
        assert "0.900" in table

    def test_all_modes_present(self) -> None:
        mode_averages = {
            "naive": {"faithfulness": 0.8, "answer_relevancy": 0.9, "context_precision": 0.7},
            "local": {"faithfulness": 0.82, "answer_relevancy": 0.88, "context_precision": 0.72},
            "global": {"faithfulness": 0.79, "answer_relevancy": 0.85, "context_precision": 0.68},
            "hybrid": {"faithfulness": 0.85, "answer_relevancy": 0.91, "context_precision": 0.75},
        }
        table = run_evals.build_markdown_table(mode_averages)
        for mode in ["naive", "local", "global", "hybrid"]:
            assert mode in table


class TestGoldSetIntegrity:
    """Sanity checks on the real gold_set.jsonl."""

    def _load_raw(self) -> list[dict[str, Any]]:
        gold_path = REPO_ROOT / "evals" / "gold_set.jsonl"
        items = []
        with gold_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    def test_exactly_20_questions(self) -> None:
        assert len(self._load_raw()) == 20

    def test_exactly_3_mini(self) -> None:
        items = self._load_raw()
        assert sum(1 for q in items if q.get("mini") is True) == 3

    def test_unique_ids(self) -> None:
        items = self._load_raw()
        ids = [q["id"] for q in items]
        assert len(ids) == len(set(ids))

    def test_ground_truths_nonempty(self) -> None:
        for q in self._load_raw():
            assert q.get("ground_truth", "").strip(), f"Empty ground_truth in {q['id']}"
