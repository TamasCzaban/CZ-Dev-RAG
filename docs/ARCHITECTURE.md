# Architecture

> Expanded component + data-flow documentation. This file is populated incrementally by implementation phases; phase 01 lays the skeleton, later phases add details as they land.

## System context

Two human users (Tamas, Zsombor) + one machine agent (Claude Code via MCP) access a single LightRAG knowledge base hosted on Tamas's RTX 3090 Windows 11 box. Remote access via Tailscale. Client documents never leave the host machine.

## Component inventory

| Component | Runtime | Purpose |
|---|---|---|
| Ollama | Windows host, native | Serves BGE-M3 (embedding) + Qwen2.5-32B (LLM) over HTTP |
| LightRAG server (`lightrag-hku[api]`) | Docker | Ingestion + retrieval + web UI + graph management |
| RAG-Anything | In-process with LightRAG | Multimodal parsing adapter |
| MinerU | In LightRAG container (CPU) | PDF/DOCX/image → structured text |
| BGE-reranker-v2-m3 | Docker (dedicated service) | Cross-encoder reranking on retrieved chunks |
| Langfuse | Docker compose (self-hosted) | Query tracing, latency + token metrics |
| MCP server | Docker | Exposes `query_kb` + `list_documents` over MCP protocol |
| Tailscale | Windows host | Mesh VPN; binds port 9621 to tailnet only |
| restic | Windows host, scheduled | Encrypted offsite backup to Backblaze B2 |

## Data flow (ingestion)

```
Source PDF → MinerU → structured blocks → LightRAG chunker
  → [Qwen2.5-32B] entity + relation extraction
  → [BGE-M3] embeddings
  → nano-vectordb + file-based graph JSON
  → Langfuse span logged
```

## Data flow (query)

```
User question (web UI or MCP)
  → LightRAG retrieval (naive | local | global | hybrid)
  → [BGE-M3] query embedding
  → top-k vector + graph neighbors
  → [BGE-reranker] rerank to top-n
  → [Qwen2.5-32B] generation with context
  → Response + Langfuse trace with {latency, tokens, retrieval hit count, mode}
```

## Storage layout

- `data/input/{client_slug}/` — raw uploaded docs (gitignored)
- `data/rag_storage/` — LightRAG working dir: entities, relations, vectors, chunk cache (gitignored)
- `examples/demo-corpus/` — synthetic docs checked into the repo
- `langfuse_data/` — Langfuse Postgres volume (gitignored)

## Trust boundaries

1. **Tailnet perimeter** — only devices in the tailnet reach port 9621 / MCP. No TLS beyond Tailscale's WireGuard.
2. **Document trust** — uploaded docs are trusted by default. Prompt injection from adversarial PDFs is out of scope for v1; mitigations (sandboxing, prompt-strip) are roadmap items.
3. **Client NDA boundary** — `.gitignore` is the enforcement for "never publish client data." CI has no access to `data/`.

## Further reading

See `docs/DECISIONS.md` for why each component was chosen over alternatives.
