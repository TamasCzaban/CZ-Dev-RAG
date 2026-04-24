# STATE

**Current phase:** 08 — GitHub Actions CI (in progress)
**Status:** phases 01–07, 09–10 merged to main; phase 08 PR being opened; phase 09 needs human restore-drill sign-off
**Last updated:** 2026-04-24

## Completed phases (merged to main)

- **Phase 01** — Bootstrap docker-compose baseline
- **Phase 02** — Demo corpus + README quickstart polish
- **Phase 03** — BGE-reranker-v2-m3 wired into retrieval
- **Phase 04** — Ingestion / delete / backup scripts
- **Phase 05** — Ragas eval harness + 20-Q gold set + auto-README table
- **Phase 06** — OCR smoke-test harness + Tesseract-hun fallback
- **Phase 07** — MCP server (query_kb + list_documents)
- **Phase 09** — Runbook: Tailscale, model pulls, backup schedule, restore drill
- **Phase 10** — Langfuse tracing module

## In progress

- **Phase 08** — GitHub Actions CI — PR being created

## Needs human action before marking complete

- **Phase 09 restore drill:** Execute `scripts/backup.sh`, delete `data/rag_storage/`, restore from restic snapshot, run sanity query. See `docs/RUNBOOK.md` § Restore drill.
- **Phase 06 OCR fixtures:** Replace synthetic stub PDFs in `evals/ocr_smoke/` with real public-domain Hungarian text scans. See `evals/ocr_smoke/README.md`.
- **Phase 08 branch protection:** After CI PR merges, set branch protection on `main` in GitHub Settings — required checks: `lint`, `typecheck`, `test`, `compose-smoke`.
- **Phase 06 host deps:** Install `tesseract-ocr` + `tesseract-ocr-hun` + `poppler-utils` on the host before running OCR smoke harness.

## Upstream backlog

| Phase | Issue | Branch | Status | Blocked by |
|---|---|---|---|---|
| 01 | [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2) | — | merged | — |
| 02 | [#3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3) | — | merged | 01 |
| 03 | [#4](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/4) | — | merged | 01 |
| 04 | [#5](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/5) | — | merged | 01, 02 |
| 05 | [#6](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/6) | — | merged | 02, 03 |
| 06 | [#7](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/7) | — | merged | 02, 04 |
| 07 | [#8](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/8) | — | merged | 01 |
| 08 | [#9](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/9) | `phase/08-ci-workflow` | in progress | 04, 05, 07 |
| 09 | [#10](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/10) | — | merged (restore drill pending) | 01, 04 |
| 10 | [#11](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/11) | — | merged | 01 |
