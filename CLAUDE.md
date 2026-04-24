# CZ-Dev-RAG — Project Instructions

## What this project is

Local knowledge base for CZ Dev agency using LightRAG + RAG-Anything. Hosted on Tamas's RTX 3090 (Windows 11 + native Ollama + Docker Desktop), shared with Zsombor via Tailscale. Public GitHub repo; client data never committed.

See `README.md` for the user-facing summary and `docs/DECISIONS.md` for why-this-not-that.
See `LEARNINGS.md` for operational gotchas — NaN embedding bugs, timeout footguns, WSL conflicts, etc. Read it before debugging any LightRAG/Ollama issue.

## Non-negotiable rules

1. **Never commit anything under `data/`, `rag_storage/`, or `*.env`.** The repo is public. Client contracts live on the 3090 box only. `.gitignore` enforces this.
2. **The demo corpus under `examples/demo-corpus/` is synthetic only.** Fake company names (AcmeCo, etc.), made-up terms, no real client data.
3. **Do not break `docker compose up` from a fresh clone.** The recruiter-runnability is the repo's primary portfolio signal.
4. **Embedding model is locked to BGE-M3.** Changing it requires reindexing everything. Don't swap it without an ADR in `docs/DECISIONS.md`.
5. **LLM is locked to Qwen2.5-32B-Instruct Q4_K_M.** Smaller models produce bad entity graphs. Don't downgrade without an ADR.

## Stack

- Python 3.11+, managed with **uv** (commit `pyproject.toml` + `uv.lock`, never `requirements.txt`)
- Docker compose orchestrates: LightRAG server, Langfuse, BGE reranker, MCP server
- Ollama runs natively on Windows host; containers reach it at `http://host.docker.internal:11434`
- Linting: `ruff`. Type-checking: `mypy`. Tests: `pytest`.

## Development workflow (GSD)

Work is tracked as phases in `ROADMAP.md`. Current phase is recorded in `STATE.md`. To work on a phase:

1. `/gsd:plan-phase NN` — generates the plan doc; nothing in the code changes
2. `/gsd:execute-phase NN` — applies code changes, runs build + checks, commits
3. `/gsd-review` — fresh-context review before PR
4. `gh pr create ...`

## Directory structure (target)

```
.
├── docker-compose.yml
├── .env.example
├── pyproject.toml
├── uv.lock
├── src/                      # Python code (MCP server, eval harness, scripts)
├── scripts/                  # ingest.py, delete_by_source.py, backup.sh
├── evals/                    # gold_set.jsonl, run_evals.py, ocr_smoke/
├── examples/demo-corpus/     # synthetic docs for recruiter demos
├── docs/                     # ARCHITECTURE.md, DECISIONS.md
├── data/                     # GITIGNORED — client input + rag_storage
└── .github/workflows/        # CI — ruff, mypy, optional eval-smoke
```

## Testing strategy defaults

- **Ingestion pipeline code:** pytest + synthetic inputs from `examples/demo-corpus/`. No real LLM calls in unit tests.
- **MCP server:** pytest with mocked LightRAG client.
- **Eval harness:** _is_ the test for retrieval quality. Runs manually against demo corpus; CI-smoke runs 3-Q mini set only.
- **OCR:** `evals/ocr_smoke/` — known input → known output, fixture-based.

## Commit + push

Tamas has pre-authorized `git push` to this repo. Create commits with Claude co-author footer. Don't skip hooks.

## Things to NOT do

- Don't add a custom web UI — LightRAG ships one, use it
- Don't add auth middleware — Tailscale is the perimeter
- Don't migrate to Neo4j in v1 — nano-vectordb + file graph handle this scale
- Don't deploy to AWS from this repo — that's a separate portfolio artifact
- Don't add Hungarian gold-set eval in v1 — bloats scope; OCR smoke test covers HU concerns
