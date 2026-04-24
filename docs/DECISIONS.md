# Architecture Decision Records

> Short, dated entries capturing significant technical choices and why they were made. New ADRs append to the bottom. Never rewrite history — if a decision changes, add a new ADR that supersedes the old one.

Format: `ADR-NNN` · short title · date · status.

---

## ADR-001 · Use LightRAG + RAG-Anything over plain vector RAG · 2026-04-24 · accepted

**Context:** The KB needs to answer complex cross-document questions ("what did we agree with BEMER about X?") where the relevant signal spans multiple docs — a plain vector RAG over chunks underperforms on this.

**Decision:** Use LightRAG's dual-level (low + high) graph-augmented retrieval. Wrap with RAG-Anything for multimodal (PDF tables, images, DOCX) ingestion.

**Alternatives considered:** GraphRAG (Microsoft) — heavier and less actively maintained for the single-node use case. LlamaIndex graph — more code to assemble, less out-of-the-box. Plain Chroma + reranker — insufficient for cross-doc reasoning.

**Consequences:** Ingestion is more expensive (entity + relation extraction runs Qwen-32B per chunk). Graph quality depends heavily on the extraction LLM — cannot cheap out on model size.

---

## ADR-002 · BGE-M3 as the embedding model · 2026-04-24 · accepted

**Context:** CZ Dev's corpus is bilingual (English + Hungarian). Embedding model must handle both well and must be free (self-hosted).

**Decision:** BGE-M3 via Ollama. MTEB 63.0, multilingual, 8K context, 568M params. Recommended by LightRAG docs.

**Alternatives considered:** Nomic Embed Text v2 (English-strong, weaker HU). Qwen3-Embedding-8B (heavier, GPU pressure against the 32B LLM). Arctic-Embed-L (English only).

**Consequences:** The embedding dimension + model version are now load-bearing — changing either requires a full reindex. Version pinned in `.env.example` as `EMBEDDING_MODEL=bge-m3:latest` with a note to replace `:latest` with an explicit digest once stable.

---

## ADR-003 · Qwen2.5-32B-Instruct Q4_K_M for extraction + generation · 2026-04-24 · accepted

**Context:** LightRAG's graph quality collapses with weak extraction LLMs — sub-14B models produce inconsistent entities. The 3090 has 24GB VRAM.

**Decision:** Qwen2.5-32B-Instruct quantized to Q4_K_M via Ollama (~18GB VRAM). Leaves ~6GB headroom for BGE-M3 + reranker.

**Alternatives considered:** Llama-3.3-70B (doesn't fit). Qwen2.5-14B (tested by others — entity brittleness). Mixtral-8x7B (slower on 3090 than Qwen-32B dense-eq). Cloud API (free-local goal conflicts).

**Consequences:** Ingestion throughput is bound by Qwen-32B's ~20 tok/sec on a 3090. ~6h for 500 dense PDFs is acceptable.

---

## ADR-004 · BGE-reranker-v2-m3 in the retrieval path · 2026-04-24 · accepted

**Context:** Modern RAG setups consistently benefit from a reranking stage after initial retrieval. Recruiters expect to see one.

**Decision:** Add BGE-reranker-v2-m3 as a dedicated docker-compose service. Called after vector + graph retrieval, before generation.

**Alternatives considered:** Cohere Rerank (paid, cloud). MonoT5 (older, weaker). No reranker (underperforms on relevance metrics).

**Consequences:** One more container to run. Latency adds ~200ms per query. Worth it for relevance gains measurable in the Ragas eval.

---

## ADR-005 · Langfuse for tracing over custom metrics file · 2026-04-24 · accepted

**Context:** Need per-query visibility into latency, token cost, retrieval quality. A custom `metrics.jsonl` + Streamlit dashboard would work but is a weaker portfolio signal.

**Decision:** Self-host Langfuse via docker-compose. Use the Python SDK to emit spans from LightRAG and the MCP server.

**Alternatives considered:** Arize Phoenix (heavier, more ML-ops-flavored). OpenTelemetry → Jaeger (more work to set up, less RAG-specific). Raw `metrics.jsonl` (weak CV signal).

**Consequences:** Adds Postgres + Langfuse web service to the compose stack. Free self-hosted; zero external dependencies.

---

## ADR-006 · Single unified graph, no per-client workspace isolation · 2026-04-24 · accepted

**Context:** The original plan considered per-client `workspace_dir` isolation for privacy. Scope was later reduced to "internal only, never client-facing."

**Decision:** One unified LightRAG graph for all CZ Dev clients + internal docs. Subfolders under `data/input/{client_slug}/` organize source documents; the graph itself is merged.

**Alternatives considered:** Per-client workspaces (rejected — dead weight for internal-only use, kills cross-client entity recognition). Per-client Neo4j DBs (over-engineering).

**Consequences:** Cross-client insights surface automatically (e.g. "same Firebase pattern used in BEMER and KEV Explorer"). If CZ Dev ever productizes this as a client-facing service, multi-tenancy is a v2 item, not a refactor.

---

## ADR-007 · Windows-native Ollama + Docker Desktop, not WSL2 / dual-boot · 2026-04-24 · accepted

**Context:** The 3090 lives in a Windows 11 box. Options: dual-boot Ubuntu, Hyper-V VM, WSL2 + GPU passthrough, or Windows-native services. Recruiter-runnability matters.

**Decision:** Ollama runs natively on Windows (uses RTX 3090 directly via CUDA). Everything else runs in Docker Desktop. Containers reach Ollama at `http://host.docker.internal:11434`.

**Alternatives considered:** Native Ubuntu dual-boot (too much friction for Tamas's day-job machine). Hyper-V with DDA GPU passthrough (consumer Win11 doesn't support well; takes GPU from host). WSL2 with GPU passthrough (works, but recruiter install path is longer).

**Consequences:** MinerU GPU acceleration on Windows is finicky — v1 runs MinerU on CPU. WSL2-MinerU-GPU upgrade is a roadmap item triggered only if ingestion time becomes painful.

---

## ADR-008 · Tailscale as the auth perimeter, no app-level auth · 2026-04-24 · accepted

**Context:** Two users (Tamas, Zsombor). Adding Cognito / Clerk / API-key middleware for two people is over-engineering. But the KB contains client contracts — it cannot be public.

**Decision:** Tailscale tailnet is the authentication + network perimeter. LightRAG binds to `0.0.0.0:9621`; Windows firewall + Tailscale ACLs restrict access to tamas + zsombor devices only. No TLS beyond Tailscale's WireGuard.

**Alternatives considered:** App-level auth (over-engineering). Cloudflare Tunnel (needs public DNS + cert management). WireGuard directly (Tailscale is strictly easier, same wire protocol).

**Consequences:** If Tamas's Tailscale auth key leaks, the KB is exposed to that device — document key rotation in the runbook. A future client-facing SaaS version would need real auth; explicitly out of v1 scope.

---

## ADR-009 · MCP server wrapper as a first-class component · 2026-04-24 · accepted

**Context:** Tamas and Zsombor use Claude Code daily. Letting Claude Code query the KB directly as a tool is higher-value than always using the web UI. It's also a differentiating portfolio signal in 2026.

**Decision:** Ship a small Python MCP server that exposes `query_kb(question, mode)` and `list_documents()`. Runs as a docker-compose service alongside LightRAG.

**Alternatives considered:** Don't ship MCP (weaker CV signal; also worse daily workflow). OpenAPI schema only (not consumable by Claude Code natively).

**Consequences:** Tamas and Zsombor can ask Claude Code "what do our CZ Dev pricing docs say about retainers?" during client work. README shows the MCP config snippet for recruiters.

---

## ADR-010 · MIT license, public repo, private data via .gitignore · 2026-04-24 · accepted

**Context:** The repo serves a dual purpose: internal tool for CZ Dev + public portfolio artifact. Client NDAs prohibit publishing contract contents.

**Decision:** Public GitHub repo under TamasCzaban/CZ-Dev-RAG, MIT licensed. Client data lives only in gitignored `data/` on the 3090 host. A synthetic `examples/demo-corpus/` ships with the repo so recruiters can run the demo without any real client material.

**Alternatives considered:** Private repo (kills portfolio signal). Two repos (public code + private data) — rejected as over-engineering; .gitignore is enough. Apache-2.0 license (equivalent; MIT is shorter + more recognizable for portfolio).

**Consequences:** CZ Dev's MSA/SOW templates gain a one-sentence clause disclosing internal AI tooling. Pre-commit hook (future phase) scans for accidental real-client filenames before push.
