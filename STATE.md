# STATE

**Current phase:** Phase 14 (next) — Tailscale rollout in progress
**Status:** 13/17 phases done (phases 01–13 complete); 3 manual items pending (see below)
**Last updated:** 2026-04-30

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
- **Phase 11** — Compose profile for client-only MCP — PR [#34](https://github.com/TamasCzaban/CZ-Dev-RAG/pull/34) merged
- **Phase 12** — File Tailscale SSH follow-up issue + update ADR-008 rollout status — PR [#36](https://github.com/TamasCzaban/CZ-Dev-RAG/pull/36) merged
- **Phase 13** — Install Tailscale on host + MagicDNS — DONE (`desktop-rh9a2o7.tailabdd49.ts.net`, IP `100.105.249.5`)

## Tailscale rollout phases (14–17) — remaining

| Phase | Branch | Status | Issue |
|-------|--------|--------|-------|
| Phase 14 [HITL] | `phase/14-tailscale-acl-device-tags` | NOT STARTED | [#30](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/30) |
| Phase 15 [HITL] | `phase/15-invite-zsombor-tailnet` | NOT STARTED | [#31](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/31) |
| Phase 16 | `phase/16-runbook-magicdns-zsombor-setup` | NOT STARTED | [#32](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/32) |
| Phase 17 [HITL] | `phase/17-e2e-smoke-test-zsombor` | NOT STARTED | [#33](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/33) |

Next executable phase: **Phase 14** [HITL — Tailscale admin console: device tagging + ACL]

---

## Manual items still pending (human action required)

| Item | What to do |
|------|-----------|
| **Phase 08 branch protection** | GitHub Settings → Branches → main → required status checks: `lint`, `typecheck`, `test`, `compose-smoke` |
| **Phase 09 restore drill** | `bash scripts/backup.sh` (with B2 creds in .env), then delete `data/rag_storage/`, restore from restic snapshot, run sanity query. See `docs/RUNBOOK.md` § Restore drill. |
| **Phase 06 OCR fixtures** | Replace stub PDFs in `evals/ocr_smoke/` with real public-domain Hungarian text scans. See `evals/ocr_smoke/README.md`. Also: install `tesseract-ocr` + `tesseract-ocr-hun` + `poppler-utils` on host. |
