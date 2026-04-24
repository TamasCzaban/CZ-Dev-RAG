# CZ-Dev-RAG — Roadmap

Phases follow the GSD (Get Shit Done) workflow. Each phase is one vertical slice — independently reviewable, PR-sized, delivers user-visible progress.

**Current phase:** see [`STATE.md`](./STATE.md).

## Phase index

_Phases are appended here as `/issue-to-gsd` is run against each slice issue. Each phase gets its own `phases/NN-slug/` directory with PLAN.md + EXECUTE.md + STATE.md._

---

## Planned phases (from PRD)

_Populated by Phase 4 of the `/idea-to-plan` pipeline. See the Decision Summary at `C:\Users\Toma\.claude\plans\abstract-tumbling-pie.md` for scope._

<!-- PHASES:START -->
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
