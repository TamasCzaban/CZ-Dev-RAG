# CZ-Dev-RAG — Roadmap

Phases follow the GSD (Get Shit Done) workflow. Each phase is one vertical slice — independently reviewable, PR-sized, delivers user-visible progress.

**Current phase:** see [`STATE.md`](./STATE.md).

## Phase index

_Phases are appended here as `/issue-to-gsd` is run against each slice issue. Each phase gets its own `phases/NN-slug/` directory with PLAN.md + EXECUTE.md + STATE.md._

---

## Planned phases (from PRD)

_Populated by Phase 4 of the `/idea-to-plan` pipeline. See the Decision Summary at `C:\Users\Toma\.claude\plans\abstract-tumbling-pie.md` for scope._

<!-- PHASES:START -->

### Phase 01 — Bootstrap docker-compose baseline
- **Issue:** [#2](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/2)
- **Branch:** `phase/01-bootstrap-compose`
- **Depends on:** _none_ (foundational)
- **Testing Strategy:** Integration smoke — docker compose up + healthcheck loop. No unit tests (pure infra). Source: this phase adds only compose YAML + `.env.example` + `pyproject.toml` stub.
- **Status:** shipped, PR open

### Phase 02 — Demo corpus + README quickstart polish
- **Issue:** [#3](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/3)
- **Branch:** `phase/02-demo-corpus-quickstart`
- **Depends on:** Phase 01
- **Testing Strategy:** None (UX / docs slice). Reason: this phase only adds static synthetic markdown docs + README prose — no code to test. Validation is the manual "recruiter 15-min runnability drill" documented in the acceptance criteria.
- **Status:** shipped, PR open (stacked on phase/01-bootstrap-compose)

### Phase 03 — BGE-reranker-v2-m3 wired into retrieval
- **Issue:** [#4](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/4)
- **Branch:** `phase/03-reranker-service`
- **Depends on:** Phase 01
- **Testing Strategy:** Unit test with fixture chunks (`tests/test_rerank.py` — mock HTTP client, assert rerank request shape + ordering of returned chunks) + integration smoke (end-to-end query triggers rerank call, verified via log assertion).
- **Status:** planned

### Phase 04 — Ingestion / delete / backup scripts
- **Issue:** [#5](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/5)
- **Branch:** `phase/04-ingest-delete-backup-scripts`
- **Depends on:** Phase 01, Phase 02 (demo corpus needed as test input)
- **Testing Strategy:** Integration tests against `examples/demo-corpus/` — `tests/test_ingest.py` asserts graph gains expected docs via LightRAG API; `tests/test_delete.py` asserts delete_by_source removes doc + entities. Manual-only for `backup.sh` (real B2 bucket required — not CI-safe).
- **Status:** planned

### Phase 05 — Ragas eval harness + 20-Q gold set + auto-README table
- **Issue:** [#6](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/6)
- **Branch:** `phase/05-ragas-eval-harness`
- **Depends on:** Phase 02 (demo corpus), Phase 03 (reranker must be in the pipeline when evals run so pillar #5 is honest)
- **Testing Strategy:** Smoke test only (`tests/test_evals.py`) — fixture 2-Q gold set + mocked LightRAG client; assert `run_evals.py --mini` writes the expected markdown table. Do NOT assert specific Ragas scores (LLM-as-judge variance makes them non-deterministic).
- **Status:** planned

### Phase 06 — OCR smoke-test harness + Tesseract-hun fallback
- **Issue:** [#7](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/7)
- **Branch:** `phase/06-ocr-smoke-tesseract`
- **Depends on:** Phase 02 (some demo docs may be shared), Phase 04 (ingestion must route through OCR engine selector)
- **Testing Strategy:** Fixture round-trip (the 5 Hungarian PDFs + expected `.txt` files ARE the test; `evals/run_ocr_smoke.py` IS the test runner — asserts ≥95% accuracy per sample). No separate unit tests for the `src/ocr/` engine-selector abstraction — it is thin and the smoke test covers end-to-end behavior.
- **Status:** planned

### Phase 07 — MCP server (query_kb + list_documents)
- **Issue:** [#8](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/8)
- **Branch:** `phase/07-mcp-server`
- **Depends on:** Phase 01
- **Testing Strategy:** Unit tests (`tests/test_mcp_server.py`) — mock LightRAG HTTP client; assert both tools return expected JSON shape given fixture responses; assert error cases (invalid mode, network failure) return structured MCP errors rather than crashing. Plus integration smoke: subprocess launches the server, MCP `tools/list` over stdio advertises both tools.
- **Status:** planned

### Phase 08 — GitHub Actions CI (ruff + mypy + compose-smoke + optional eval-smoke)
- **Issue:** [#9](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/9)
- **Branch:** `phase/08-ci-workflow`
- **Depends on:** Phase 04, Phase 05, Phase 07 (needs real code to lint + type-check; can land incrementally earlier with just compose-smoke + lint but the merge gate is defined here)
- **Testing Strategy:** The workflow itself IS the test — validation is pushing a known-failing commit to a throwaway branch and confirming CI fails for the right reason. Don't add tests of the CI config itself.
- **Status:** planned

### Phase 09 — Runbook — Tailscale, model pulls, backup schedule, restore drill
- **Issue:** [#10](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/10)
- **Branch:** `phase/09-runbook-tailscale`
- **Depends on:** Phase 01, Phase 04 (must document real commands for services + scripts that actually exist)
- **Testing Strategy:** None (docs-only slice). Reason: no code added. Validation is a fresh-eyes drill — Zsombor follows the Tailscale + query sections on a clean machine without additional guidance; restore drill executed once manually before marking the phase done.
- **Status:** planned

### Phase 10 — Langfuse tracing wiring
- **Issue:** [#11](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/11)
- **Branch:** `phase/10-langfuse-tracing`
- **Depends on:** Phase 01 (Langfuse service); integrates with Phase 07 (MCP spans) — order flexible, either lands first and Phase 07 adds MCP spans, or Phase 07 lands first and this phase adds spans to it
- **Testing Strategy:** Unit test (`tests/test_tracing.py`) — mock Langfuse client, assert `trace_query` emits span with expected shape (fields present, types correct). Integration smoke — run a demo query, assert a new span appears in Langfuse within 5s.
- **Status:** planned

### Phase 11 — Compose profile for client-only MCP
- **Issue:** [#27](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/27)
- **Branch:** `phase/11-compose-client-mcp-profile`
- **Depends on:** _none_
- **Testing Strategy:** Integration smoke — `docker compose up mcp --no-deps -d` on a machine without a local LightRAG stack; verify no dependent containers (lightrag, reranker, langfuse) are started. Source: `docker-compose.yml` `mcp` service. If `--no-deps` is insufficient, `profiles: [client]` is added and the same check is re-run.
- **Status:** NOT STARTED

### Phase 12 — File Tailscale SSH follow-up issue + update ADR-008 rollout status
- **Issue:** [#28](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/28)
- **Branch:** `phase/12-tailscale-ssh-issue-adr008`
- **Depends on:** _none_ (can run any time; ideally after rollout is complete so the ADR-008 date is real)
- **Testing Strategy:** None (docs-only + GH issue creation). Reason: this phase appends text to `docs/DECISIONS.md` and creates one GitHub issue — no code changed, no runtime behaviour.
- **Status:** NOT STARTED

### Phase 13 — Install Tailscale on host + enable MagicDNS [HITL]
- **Issue:** [#29](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/29)
- **Branch:** `phase/13-install-tailscale-magicdns`
- **Depends on:** _none_
- **Testing Strategy:** None (HITL infra slice). Reason: involves OS-level installer + browser-based SSO auth; no automated test possible. Validation is manual: `tailscale status` shows host with MagicDNS hostname.
- **Status:** NOT STARTED

### Phase 14 — Tailscale admin — device tagging + tag-based ACL [HITL]
- **Issue:** [#30](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/30)
- **Branch:** `phase/14-tailscale-acl-device-tags`
- **Depends on:** Phase 13
- **Testing Strategy:** None (HITL admin console). Reason: ACL JSON is entered in the Tailscale web console, not a file in this repo. Validation is manual: `curl http://<tailnet-host>:9621/health` from a `tag:rag-user` device returns 200.
- **Status:** NOT STARTED

### Phase 15 — Invite Zsombor to tailnet via Google SSO + assign tag:rag-user [HITL]
- **Issue:** [#31](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/31)
- **Branch:** `phase/15-invite-zsombor-tailnet`
- **Depends on:** Phase 13, Phase 14
- **Testing Strategy:** None (HITL — requires human action on Zsombor's machine). Validation: `tailscale status` on Tamas's host shows Zsombor's device as a peer; `curl` from Zsombor's machine returns HTTP 200 on port 9621.
- **Status:** NOT STARTED

### Phase 16 — Update RUNBOOK.md — MagicDNS hostname + Zsombor first-time setup section
- **Issue:** [#32](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/32)
- **Branch:** `phase/16-runbook-magicdns-zsombor-setup`
- **Depends on:** Phase 11, Phase 13, Phase 15
- **Testing Strategy:** None (docs-only slice). Reason: `docs/RUNBOOK.md` markdown updates only; CI ruff/mypy passes trivially. Validation is human-readability check + used directly in Phase 17 smoke test.
- **Status:** NOT STARTED

### Phase 17 — End-to-end smoke test from Zsombor's clean machine [HITL]
- **Issue:** [#33](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/33)
- **Branch:** `phase/17-e2e-smoke-test-zsombor`
- **Depends on:** Phase 11, Phase 13, Phase 14, Phase 15, Phase 16
- **Testing Strategy:** None (HITL — real Zsombor on a real machine). This phase IS the integration test for the entire Tailscale rollout. Acceptance criteria: ingest of demo-corpus exits 0, MCP query_kb returns non-empty answer, ACL negative test passes. No automated proxy.
- **Status:** NOT STARTED

<!-- PHASES:END -->

## Out of scope for v1

Flagged here so recruiters can see the intentional boundary:

- Neo4j backend (file-based graph handles current scale)
- Multi-tenant ACLs (single unified graph by design)
- AWS deployment (separate portfolio artifact)
- Custom web UI beyond LightRAG's built-in
- Auth layer beyond Tailscale
- Reranker fine-tuning
- Streaming / incremental ingestion
- Hungarian gold-set eval (OCR smoke test covers HU)
- Observability dashboards beyond Langfuse defaults
