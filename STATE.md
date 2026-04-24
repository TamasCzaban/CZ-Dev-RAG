# STATE

**Current phase:** 03 — BGE-reranker-v2-m3 wired into retrieval
**Status:** phases 01 + 02 shipped (PRs open, awaiting review)
**Branch for phase 03:** `phase/03-reranker-service`
**Last updated:** 2026-04-24

## Completed phases

- **Phase 01** — Bootstrap docker-compose baseline — PR open for [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2) on `phase/01-bootstrap-compose`. `docker compose config` validates.
- **Phase 02** — Demo corpus + README quickstart polish — PR open for [#3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3) on `phase/02-demo-corpus-quickstart`, stacked on top of phase 01.

## Next up

Phase 03 — see [ROADMAP.md](./ROADMAP.md#phase-03--bge-reranker-v2-m3-wired-into-retrieval) and [issue #4](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/4).

To begin: `/gsd:plan-phase 03` → review → `/gsd:execute-phase 03` → `/gsd-review` → `gh pr create`.

## Upstream backlog

| Phase | Issue | Branch | Status | Blocked by |
|---|---|---|---|---|
| 01 | [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2) | `phase/01-bootstrap-compose` | shipped, PR open | — |
| 02 | [#3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3) | `phase/02-demo-corpus-quickstart` | shipped, PR open | 01 |
| 03 | [#4](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/4) | `phase/03-reranker-service` | planned | 01 |
| 04 | [#5](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/5) | `phase/04-ingest-delete-backup-scripts` | planned | 01, 02 |
| 05 | [#6](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/6) | `phase/05-ragas-eval-harness` | planned | 02, 03 |
| 06 | [#7](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/7) | `phase/06-ocr-smoke-tesseract` | planned | 02, 04 |
| 07 | [#8](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/8) | `phase/07-mcp-server` | planned | 01 |
| 08 | [#9](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/9) | `phase/08-ci-workflow` | planned | 04, 05, 07 |
| 09 | [#10](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/10) | `phase/09-runbook-tailscale` | planned | 01, 04 |
| 10 | [#11](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/11) | `phase/10-langfuse-tracing` | planned | 01 (integrates with 07) |
