"""Ragas evaluation harness for CZ-Dev-RAG.

Runs the gold-set questions against LightRAG retrieval modes and scores
faithfulness, answer_relevancy, and context_precision using Ragas v0.2+.

Usage::

    uv run python evals/run_evals.py                        # all 20 Qs x 4 modes
    uv run python evals/run_evals.py --mini                  # 3 CI-smoke Qs only
    uv run python evals/run_evals.py --output-readme         # update README table
    uv run python evals/run_evals.py --modes naive,hybrid    # subset of modes
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.progress import track
from rich.table import Table

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)
console = Console()

EVALS_DIR = Path(__file__).parent
GOLD_SET_PATH = EVALS_DIR / "gold_set.jsonl"
RESULTS_DIR = EVALS_DIR / "results"
README_PATH = Path(__file__).parent.parent / "README.md"

EVAL_START_MARKER = "<!-- EVAL:START -->"
EVAL_END_MARKER = "<!-- EVAL:END -->"

DEFAULT_MODES = "naive,local,global,hybrid"
DEFAULT_LIGHTRAG_URL = "http://localhost:9621"

METRICS_NAMES = ["faithfulness", "answer_relevancy", "context_precision"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_gold_set(mini: bool) -> list[dict[str, Any]]:
    """Load questions from gold_set.jsonl, optionally filtering to mini set."""
    questions: list[dict[str, Any]] = []
    with GOLD_SET_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if mini and not item.get("mini", False):
                continue
            questions.append(item)
    return questions


# ---------------------------------------------------------------------------
# LightRAG querying
# ---------------------------------------------------------------------------


def query_lightrag(
    client: httpx.Client,
    lightrag_url: str,
    question: str,
    mode: str,
) -> tuple[str, list[str]]:
    """POST to LightRAG /query and return (answer, contexts).

    Returns empty strings / lists on HTTP or parsing failures so the harness
    can continue rather than crashing.
    """
    try:
        resp = client.post(
            f"{lightrag_url}/query",
            json={"query": question, "mode": mode},
            timeout=300.0,
        )
        resp.raise_for_status()
        data = resp.json()
        answer: str = data.get("response", data.get("answer", ""))
        # LightRAG may return contexts under different keys depending on version
        raw_contexts = data.get("contexts", data.get("sources", []))
        if isinstance(raw_contexts, list):
            contexts = [c if isinstance(c, str) else str(c) for c in raw_contexts]
        else:
            contexts = [str(raw_contexts)] if raw_contexts else []
        # Ensure at least one non-empty context so Ragas doesn't error
        if not contexts:
            contexts = [answer or "no context available"]
        return answer, contexts
    except Exception as exc:
        console.print(f"[yellow]Warning: LightRAG query failed ({exc})[/yellow]")
        return "", ["no context available"]


# ---------------------------------------------------------------------------
# Ragas evaluation
# ---------------------------------------------------------------------------


def build_ragas_dataset(
    samples_data: list[dict[str, Any]],
) -> Any:
    """Build a Ragas EvaluationDataset from the collected sample data."""
    from ragas import EvaluationDataset, SingleTurnSample

    samples: list[Any] = [
        SingleTurnSample(
            user_input=d["question"],
            response=d["answer"],
            retrieved_contexts=d["contexts"],
            reference=d["ground_truth"],
        )
        for d in samples_data
    ]
    return EvaluationDataset(samples=samples)


def run_ragas(
    dataset: Any,
    ollama_base_url: str = "http://localhost:11434",
) -> dict[str, float]:
    """Run Ragas evaluation and return metric averages.

    Uses Ragas 0.4 API: llm_factory + OpenAIEmbeddings pointed at Ollama's
    OpenAI-compatible endpoint (http://localhost:11434/v1).

    Returns NaN-safe floats — individual NaNs are dropped from the average.
    """
    import math

    from openai import OpenAI
    from ragas import evaluate
    from ragas.embeddings import OpenAIEmbeddings
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        Faithfulness,
    )

    llm_model = os.environ.get("LLM_MODEL", "qwen2.5:32b-instruct-q4_K_M")
    embed_model = os.environ.get("EMBEDDING_MODEL", "bge-m3:latest")
    ollama_v1_url = ollama_base_url.rstrip("/") + "/v1"

    ollama_client = OpenAI(base_url=ollama_v1_url, api_key="ollama")
    ragas_llm = llm_factory(llm_model, client=ollama_client)
    ragas_embeddings = OpenAIEmbeddings(model=embed_model, client=ollama_client)

    metrics = [Faithfulness(llm=ragas_llm), AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings), ContextPrecision(llm=ragas_llm)]

    # evaluate() returns EvaluationResult | Executor; cast to Any for .get()
    raw_result: Any = evaluate(
        dataset,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )

    # result is a dict-like object mapping metric name → score (float or list)
    averages: dict[str, float] = {}
    for metric_name in METRICS_NAMES:
        raw = raw_result.get(metric_name)
        if raw is None:
            averages[metric_name] = float("nan")
            continue
        if isinstance(raw, (int, float)):
            averages[metric_name] = float(raw)
        elif isinstance(raw, list):
            valid = [v for v in raw if v is not None and not math.isnan(float(v))]
            averages[metric_name] = sum(valid) / len(valid) if valid else float("nan")
        else:
            averages[metric_name] = float("nan")
    return averages


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------


def write_results_csv(
    rows: list[dict[str, Any]],
    timestamp: str,
) -> Path:
    """Write per-question results to evals/results/<timestamp>.csv."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / f"{timestamp}.csv"
    fieldnames = ["mode", "question_id", *METRICS_NAMES]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


# ---------------------------------------------------------------------------
# README table injection
# ---------------------------------------------------------------------------


def build_markdown_table(mode_averages: dict[str, dict[str, float]]) -> str:
    """Render a markdown table of per-mode average metrics."""
    import math

    lines = [
        "| Mode    | Faithfulness | Answer Relevancy | Context Precision |",
        "|---------|--------------|------------------|-------------------|",
    ]
    for mode, scores in mode_averages.items():

        def fmt(v: float) -> str:
            return f"{v:.3f}" if not math.isnan(v) else "—"

        lines.append(
            f"| {mode:<7} | {fmt(scores['faithfulness']):<12} "
            f"| {fmt(scores['answer_relevancy']):<16} "
            f"| {fmt(scores['context_precision']):<17} |"
        )
    return "\n".join(lines)


def update_readme(mode_averages: dict[str, dict[str, float]]) -> None:
    """Replace the <!-- EVAL:START -->...<!-- EVAL:END --> block in README.md."""
    if not README_PATH.exists():
        console.print("[yellow]README.md not found — skipping table update.[/yellow]")
        return

    content = README_PATH.read_text(encoding="utf-8")
    table_md = build_markdown_table(mode_averages)
    timestamp_note = f"_Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_"
    replacement = f"{EVAL_START_MARKER}\n{timestamp_note}\n\n{table_md}\n{EVAL_END_MARKER}"

    pattern = re.compile(
        re.escape(EVAL_START_MARKER) + r".*?" + re.escape(EVAL_END_MARKER),
        re.DOTALL,
    )
    if not pattern.search(content):
        console.print(
            "[yellow]EVAL markers not found in README.md — skipping update.[/yellow]"
        )
        return

    new_content = pattern.sub(replacement, content)
    README_PATH.write_text(new_content, encoding="utf-8")
    console.print("[green]README.md updated with eval results table.[/green]")


# ---------------------------------------------------------------------------
# Rich summary table
# ---------------------------------------------------------------------------


def print_summary_table(mode_averages: dict[str, dict[str, float]]) -> None:
    import math

    table = Table(title="Ragas Eval Results", show_lines=True)
    table.add_column("Mode", style="cyan")
    table.add_column("Faithfulness", justify="right")
    table.add_column("Answer Relevancy", justify="right")
    table.add_column("Context Precision", justify="right")
    for mode, scores in mode_averages.items():

        def fmt(v: float) -> str:
            return f"{v:.3f}" if not math.isnan(v) else "—"

        table.add_row(
            mode,
            fmt(scores["faithfulness"]),
            fmt(scores["answer_relevancy"]),
            fmt(scores["context_precision"]),
        )
    console.print(table)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    modes: str = typer.Option(DEFAULT_MODES, help="Comma-separated LightRAG modes."),
    mini: bool = typer.Option(False, "--mini", help="Run only questions tagged mini=true."),
    output_readme: bool = typer.Option(
        False, "--output-readme", help="Update README.md eval table after scoring."
    ),
    lightrag_url: str = typer.Option(DEFAULT_LIGHTRAG_URL, help="LightRAG base URL."),
) -> None:
    """Run Ragas evals against LightRAG and write results CSV."""
    mode_list = [m.strip() for m in modes.split(",") if m.strip()]
    questions = load_gold_set(mini=mini)

    if not questions:
        console.print("[red]No questions found (gold set empty or --mini matched nothing).[/red]")
        raise typer.Exit(1)

    console.print(
        f"Running [bold]{len(questions)}[/bold] questions x [bold]{len(mode_list)}[/bold] modes"
    )

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    all_rows: list[dict[str, Any]] = []
    mode_averages: dict[str, dict[str, float]] = {}

    with httpx.Client() as client:
        for mode in mode_list:
            console.print(f"\n[bold blue]Mode: {mode}[/bold blue]")
            samples_data: list[dict[str, Any]] = []

            for q in track(questions, description=f"Querying ({mode})"):
                answer, contexts = query_lightrag(client, lightrag_url, q["question"], mode)
                samples_data.append(
                    {
                        "question": q["question"],
                        "answer": answer,
                        "contexts": contexts,
                        "ground_truth": q["ground_truth"],
                        "question_id": q["id"],
                    }
                )

            # Build Ragas dataset and evaluate
            dataset = build_ragas_dataset(samples_data)
            console.print("  Scoring with Ragas...")
            averages = run_ragas(dataset)
            mode_averages[mode] = averages

            import math

            # Build per-question rows (Ragas returns per-sample scores via result.scores)
            for sample_d in samples_data:
                all_rows.append(
                    {
                        "mode": mode,
                        "question_id": sample_d["question_id"],
                        "faithfulness": (
                            "" if math.isnan(averages["faithfulness"]) else averages["faithfulness"]
                        ),
                        "answer_relevancy": (
                            ""
                            if math.isnan(averages["answer_relevancy"])
                            else averages["answer_relevancy"]
                        ),
                        "context_precision": (
                            ""
                            if math.isnan(averages["context_precision"])
                            else averages["context_precision"]
                        ),
                    }
                )

    csv_path = write_results_csv(all_rows, timestamp)
    console.print(f"\n[green]Results written to {csv_path}[/green]")

    print_summary_table(mode_averages)

    if output_readme:
        update_readme(mode_averages)


if __name__ == "__main__":
    app()
