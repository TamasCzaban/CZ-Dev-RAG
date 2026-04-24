# Eval Harness

Automated retrieval-quality evaluation for CZ-Dev-RAG using [Ragas](https://docs.ragas.io) v0.2+.

## Overview

The harness:
1. Loads questions from `gold_set.jsonl`
2. Posts each question to LightRAG in each requested retrieval mode (`naive`, `local`, `global`, `hybrid`)
3. Scores answers and retrieved contexts with Ragas metrics
4. Writes per-question results to `evals/results/<timestamp>.csv`
5. Optionally updates the `README.md` eval table

## Running evals

All commands assume the LightRAG stack is running (`docker compose up -d`) and the demo corpus has been ingested.

```bash
# Full run — 20 questions × 4 modes
uv run python evals/run_evals.py

# CI smoke — 3 mini questions only
uv run python evals/run_evals.py --mini

# Subset of modes
uv run python evals/run_evals.py --modes naive,hybrid

# Run and update the README table
uv run python evals/run_evals.py --output-readme

# Non-default LightRAG URL (e.g. remote via Tailscale)
uv run python evals/run_evals.py --lightrag-url http://100.x.x.x:9621
```

## Ragas metrics explained

| Metric | What it measures | Range |
|---|---|---|
| **Faithfulness** | Is every claim in the answer grounded in the retrieved contexts? | 0–1 (higher = better) |
| **Answer Relevancy** | Does the answer actually address the question? | 0–1 (higher = better) |
| **Context Precision** | Are the most relevant chunks ranked higher by the retriever? | 0–1 (higher = better) |

All three metrics use the Qwen2.5-32B LLM running in local Ollama. Expect each full run (~80 LLM calls) to take 15–30 minutes on an RTX 3090.

NaN scores are displayed as `—` and excluded from averages. They appear when:
- LightRAG returned an empty answer
- The LLM failed to produce a parseable Ragas verdict

## Gold set structure

`gold_set.jsonl` — one JSON object per line:

```json
{
  "id": "q01",
  "question": "What are the payment terms in the AcmeCo MSA?",
  "ground_truth": "Invoices are due net thirty days...",
  "relevant_doc_ids": ["acmeco-msa"],
  "mini": true
}
```

Fields:

- `id` — unique question identifier (`q01`–`q20`)
- `question` — the natural-language query
- `ground_truth` — a 1–2 sentence factual answer derivable from the referenced docs
- `relevant_doc_ids` — which demo corpus documents contain the answer
- `mini` — `true` for questions included in the CI smoke run (3 of 20)

Questions cover payment terms, contract scope, tech decisions, pricing, and multilingual retrieval across all five demo corpus documents.

## Adding new questions

1. Open `evals/gold_set.jsonl`
2. Append a new JSON line following the structure above
3. Set `"mini": false` unless it should be part of the CI smoke subset
4. The question must be answerable from one or more documents in `examples/demo-corpus/`
5. Run `uv run python evals/run_evals.py --mini` to verify the harness still works

## Results CSV format

`evals/results/<timestamp>.csv` columns:

| Column | Description |
|---|---|
| `mode` | LightRAG retrieval mode |
| `question_id` | Gold-set question ID |
| `faithfulness` | Ragas faithfulness score (or empty if NaN) |
| `answer_relevancy` | Ragas answer relevancy score (or empty if NaN) |
| `context_precision` | Ragas context precision score (or empty if NaN) |

## CI integration

The GitHub Actions workflow runs `--mini` against a mocked LightRAG (no live stack required):

```yaml
- name: Eval smoke test
  run: uv run pytest tests/test_evals.py -q
```

The full eval run is manual-only (requires the live Ollama + LightRAG stack).
