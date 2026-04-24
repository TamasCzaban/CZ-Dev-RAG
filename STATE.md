# STATE

**Current phase:** complete — all 10 phases shipped
**Status:** 10/10 phases merged to main; CI green; 3 manual items pending (see below)
**Last updated:** 2026-04-24

## All phases merged to main

- **Phase 01** — Bootstrap docker-compose baseline
- **Phase 02** — Demo corpus + README quickstart polish
- **Phase 03** — BGE-reranker-v2-m3 wired into retrieval
- **Phase 04** — Ingestion / delete / backup scripts
- **Phase 05** — Ragas eval harness + 20-Q gold set + auto-README table
- **Phase 06** — OCR smoke-test harness + Tesseract-hun fallback
- **Phase 07** — MCP server (query_kb + list_documents)
- **Phase 08** — GitHub Actions CI (lint, typecheck, test, compose-smoke)
- **Phase 09** — Runbook: Tailscale, model pulls, backup schedule, restore drill
- **Phase 10** — Langfuse tracing module

## Manual items still pending (human action required)

| Item | What to do |
|------|-----------|
| **Phase 08 branch protection** | GitHub Settings → Branches → main → required status checks: `lint`, `typecheck`, `test`, `compose-smoke` |
| **Phase 09 restore drill** | `bash scripts/backup.sh` (with B2 creds in .env), then delete `data/rag_storage/`, restore from restic snapshot, run sanity query. See `docs/RUNBOOK.md` § Restore drill. |
| **Phase 06 OCR fixtures** | Replace stub PDFs in `evals/ocr_smoke/` with real public-domain Hungarian text scans. See `evals/ocr_smoke/README.md`. Also: install `tesseract-ocr` + `tesseract-ocr-hun` + `poppler-utils` on host. |
