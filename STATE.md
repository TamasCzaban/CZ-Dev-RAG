# STATE

**Current phase:** phases 03, 04, 07, 10 — PRs open, awaiting review
**Status:** phases 01 + 02 shipped (merged to main); phases 03, 04, 07, 10 implemented, PRs open
**Last updated:** 2026-04-24

## Completed phases

- **Phase 01** — Bootstrap docker-compose baseline — merged to main
- **Phase 02** — Demo corpus + README quickstart polish — merged to main
- **Phase 03** — BGE-reranker-v2-m3 wired into retrieval — PR #15 open on `phase/03-reranker-service`
- **Phase 04** — Ingestion / delete / backup scripts — PR #16 open on `phase/04-ingest-delete-backup-scripts`
- **Phase 07** — MCP server (query_kb + list_documents) — PR #17 open on `phase/07-mcp-server`
- **Phase 10** — Langfuse tracing module — PR #18 open on `phase/10-langfuse-tracing`

## Next up

After PRs 15–18 merge:
- **Phase 05** — Ragas eval harness (unblocked by 02 + 03)
- **Phase 06** — OCR smoke-test harness (unblocked by 02 + 04)
- **Phase 09** — Runbook: Tailscale, model pulls, backup schedule (unblocked by 01 + 04)

After 05 + 07 merge:
- **Phase 08** — GitHub Actions CI (unblocked by 04 + 05 + 07)

## Upstream backlog

| Phase | Issue | Branch | Status | Blocked by |
|---|---|---|---|---|
| 01 | [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2) | `phase/01-bootstrap-compose` | merged | — |
| 02 | [#3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3) | `phase/02-demo-corpus-quickstart` | merged | 01 |
| 03 | [#4](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/4) | `phase/03-reranker-service` | PR #15 open | 01 |
| 04 | [#5](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/5) | `phase/04-ingest-delete-backup-scripts` | PR #16 open | 01, 02 |
| 05 | [#6](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/6) | `phase/05-ragas-eval-harness` | planned | 02, 03 |
| 06 | [#7](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/7) | `phase/06-ocr-smoke-tesseract` | planned | 02, 04 |
| 07 | [#8](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/8) | `phase/07-mcp-server` | PR #17 open | 01 |
| 08 | [#9](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/9) | `phase/08-ci-workflow` | planned | 04, 05, 07 |
| 09 | [#10](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/10) | `phase/09-runbook-tailscale` | planned | 01, 04 |
| 10 | [#11](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/11) | `phase/10-langfuse-tracing` | PR #18 open | 01 |
