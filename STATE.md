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

## Tailscale rollout phases (11–17) — NEW

| Phase | Branch | Status | Issue |
|-------|--------|--------|-------|
| Phase 11 | `phase/11-compose-client-mcp-profile` | NOT STARTED | [#27](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/27) |
| Phase 12 | `phase/12-tailscale-ssh-issue-adr008` | NOT STARTED | [#28](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/28) |
| Phase 13 [HITL] | `phase/13-install-tailscale-magicdns` | NOT STARTED | [#29](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/29) |
| Phase 14 [HITL] | `phase/14-tailscale-acl-device-tags` | NOT STARTED | [#30](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/30) |
| Phase 15 [HITL] | `phase/15-invite-zsombor-tailnet` | NOT STARTED | [#31](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/31) |
| Phase 16 | `phase/16-runbook-magicdns-zsombor-setup` | NOT STARTED | [#32](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/32) |
| Phase 17 [HITL] | `phase/17-e2e-smoke-test-zsombor` | NOT STARTED | [#33](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/33) |

Next executable phase: **Phase 11** (or Phase 12 — both have no blockers and can run in parallel)

---

## Manual items still pending (human action required)

| Item | What to do |
|------|-----------|
| **Phase 08 branch protection** | GitHub Settings → Branches → main → required status checks: `lint`, `typecheck`, `test`, `compose-smoke` |
| **Phase 09 restore drill** | `bash scripts/backup.sh` (with B2 creds in .env), then delete `data/rag_storage/`, restore from restic snapshot, run sanity query. See `docs/RUNBOOK.md` § Restore drill. |
| **Phase 06 OCR fixtures** | Replace stub PDFs in `evals/ocr_smoke/` with real public-domain Hungarian text scans. See `evals/ocr_smoke/README.md`. Also: install `tesseract-ocr` + `tesseract-ocr-hun` + `poppler-utils` on host. |
