# STATE

**Current phase:** 02 — Demo corpus + README quickstart polish
**Status:** phase 01 shipped (PR open, awaiting review)
**Branch for phase 02:** `phase/02-demo-corpus-quickstart`
**Last updated:** 2026-04-24

## Completed phases

- **Phase 01** — Bootstrap docker-compose baseline — PR open for [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2) on `phase/01-bootstrap-compose`. `docker compose config` validates.

## Next up

Phase 02 — see [ROADMAP.md](./ROADMAP.md#phase-02--demo-corpus--readme-quickstart-polish) and [issue #3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3).

To begin: `/gsd:plan-phase 01` → review plan → `/gsd:execute-phase 01` → `/gsd-review` → `gh pr create ...`

## Upstream backlog

All 10 phases are scaffolded with feature branches + ROADMAP entries + GitHub issues:

| Phase | Issue | Branch | Blocked by |
|---|---|---|---|
| 01 | [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2) | `phase/01-bootstrap-compose` | — |
| 02 | [#3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3) | `phase/02-demo-corpus-quickstart` | 01 |
| 03 | [#4](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/4) | `phase/03-reranker-service` | 01 |
| 04 | [#5](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/5) | `phase/04-ingest-delete-backup-scripts` | 01, 02 |
| 05 | [#6](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/6) | `phase/05-ragas-eval-harness` | 02, 03 |
| 06 | [#7](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/7) | `phase/06-ocr-smoke-tesseract` | 02, 04 |
| 07 | [#8](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/8) | `phase/07-mcp-server` | 01 |
| 08 | [#9](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/9) | `phase/08-ci-workflow` | 04, 05, 07 |
| 09 | [#10](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/10) | `phase/09-runbook-tailscale` | 01, 04 |
| 10 | [#11](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/11) | `phase/10-langfuse-tracing` | 01 (integrates with 07) |
