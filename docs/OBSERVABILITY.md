# Observability — Langfuse Query Tracing

Every query that flows through the `trace_query` context manager emits a
Langfuse span. This doc explains what is traced, how to open the UI, what
each field means, and how to interpret the latency histogram.

## Opening the Langfuse UI

```
http://localhost:3000
```

On first visit create an organisation and project. Copy the project's API
keys into your `.env`:

```env
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

Then restart the stack so the MCP server (phase 07) picks up the new keys:

```bash
docker compose restart
```

## What is traced

Each query creates one **Trace** with one child **Generation** in Langfuse.

### Trace-level fields

| Field | Type | Description |
|---|---|---|
| `name` | string | Always `"lightrag.query"` (overridable via `name=` kwarg). |
| `input` | string | The raw question sent to LightRAG. |
| `output` | string | The answer returned by LightRAG. |
| `metadata.mode` | string | Retrieval mode: `naive`, `local`, `global`, or `hybrid`. |
| `metadata.latency_ms` | int | Wall-clock query time in milliseconds. |
| `metadata.tokens_in` | int | Prompt token count (from LightRAG response, if available). |
| `metadata.tokens_out` | int | Completion token count (from LightRAG response, if available). |
| `metadata.num_retrieved` | int | Number of source chunks returned before reranking. |
| `metadata.rerank_applied` | bool | Whether the BGE-reranker-v2-m3 pass was applied. |

### Generation-level fields

| Field | Type | Description |
|---|---|---|
| `name` | string | `"query"` |
| `input` | string | The question (same as trace input). |
| `model` | string | `"qwen2.5:32b-instruct-q4_K_M"` — the LLM that generated the answer. |
| `usage.input` | int | Prompt tokens. |
| `usage.output` | int | Completion tokens. |
| `output` | string | The answer. |

## No-op mode

When `LANGFUSE_PUBLIC_KEY` is empty, `init_tracing` returns `None` and
`trace_query` is a silent no-op. The query pipeline functions identically;
no Langfuse calls are made and no exceptions are raised. This is the default
for fresh clones.

## Reading the latency histogram

In the Langfuse UI navigate to **Traces → Metrics → latency_ms** (custom
metadata). A bimodal distribution is normal:

- **Fast cluster (~500–1500 ms):** `naive` mode — pure vector search, no
  graph traversal.
- **Slow cluster (~3000–8000 ms):** `local`, `global`, `hybrid` — graph
  traversal + Qwen2.5-32B generation on an RTX 3090.

Spikes above 15 s usually indicate Ollama queue saturation (another ingest
job running). Check `docker compose logs lightrag` for timeout warnings.

## Screenshot

_[Screenshot placeholder — add after first successful trace]_
