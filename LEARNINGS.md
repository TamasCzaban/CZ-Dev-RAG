# CZ-Dev-RAG — Operational Learnings

Gotchas, footguns, and non-obvious behaviours discovered in production.
Kept here so Claude and future maintainers don't repeat the same debug sessions.

> **Structure:** one file until it gets fat. When a section exceeds ~200 lines,
> split into `docs/learnings/TOPIC.md` and add a routing table here.

---

## LightRAG + Ollama on Windows (RTX 3090)

### OLLAMA_HOST env var collision
**Problem:** Windows users often set `OLLAMA_HOST=0.0.0.0` in the registry so
`ollama serve` binds to all interfaces. Docker Compose interpolates this env var
into container environment — `LLM_BINDING_HOST=${OLLAMA_HOST}` would give
containers `0.0.0.0` instead of `http://host.docker.internal:11434`.

**Fix:** Hardcode the container-side URL directly in `docker-compose.yml`:
```yaml
LLM_BINDING_HOST: http://host.docker.internal:11434
```
Never interpolate `$OLLAMA_HOST` in compose. Document this in `.env.example`.

---

### WSL Ollama vs Windows Ollama conflict
**Problem:** Docker Desktop starts WSL2. If Ollama is also installed inside WSL
and its systemd service is enabled, `wslrelay.exe` bridges WSL's
`127.0.0.1:11434` to the Windows host. Docker's `host.docker.internal` routes
to `127.0.0.1` preferentially — hitting the WSL Ollama, not the Windows one.
The WSL Ollama only has whichever models were pulled inside WSL, causing
`model not found` errors even though the right models exist in Windows Ollama.

**Diagnosis:** `netstat -an | grep 11434` shows two listeners. Ollama HTTP API
at `localhost:11434/api/tags` shows the wrong model list.

**Fix (permanent):** Disable WSL Ollama's systemd service:
```bash
wsl -- sudo systemctl disable --now ollama
wsl --shutdown
```
After this, only the Windows Ollama process (`ollama.exe`) owns port 11434 on
all interfaces, and containers route correctly via `host.docker.internal`.

**Note:** Docker Desktop auto-restarts WSL on next boot, but WSL Ollama won't
start because systemd service is disabled.

---

### LightRAG image has no `curl` — healthcheck breaks
**Problem:** `ghcr.io/hkuds/lightrag:latest` doesn't ship `curl`. A
healthcheck using `curl http://localhost:9621/health` fails immediately, causing
the container to be marked unhealthy on every boot.

**Fix:** Use Python's stdlib instead:
```yaml
healthcheck:
  test: ["CMD-SHELL", "python -c \"import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:9621/health', timeout=5).status==200 else 1)\""]
```

---

### LightRAG `ollama list` CLI shows wrong model count
**Symptom:** `ollama list` on Windows 0.17.x shows only 1–2 models even when
5+ are pulled.

**Reality:** The HTTP API is correct: `curl localhost:11434/api/tags` returns all
models. LightRAG uses the HTTP API, not the CLI. Not a real issue.

---

## LightRAG Timeout Configuration — Three Separate Systems

LightRAG has **three independent timeout mechanisms** that must all be configured
correctly. Setting one does not affect the others.

### 1. `TIMEOUT` — httpx client timeout (server CLI arg)
Controls how long the httpx HTTP client waits for Ollama to respond.

- `TIMEOUT=0` → passed as `0` to the Ollama adapter → `if timeout == 0: timeout = None` → `httpx.AsyncClient(timeout=None)` → **no HTTP timeout**. This is correct.
- Default: 300s (5 min). Too short for Qwen2.5-32B entity extraction under concurrency.
- **Set to `0` in `docker-compose.yml`** (`TIMEOUT: 0` — hardcoded, not from `.env`).

### 2. `LLM_TIMEOUT` — LightRAG worker-level timeout
Controls `asyncio.wait_for()` inside LightRAG's worker queue (`lightrag.utils.wait_func`).
The worker sets `max_execution_timeout = LLM_TIMEOUT * 2`.

**FOOTGUN: `LLM_TIMEOUT=0` means timeout after 0 seconds**, not infinite.
`0 * 2 = 0` → `asyncio.wait_for(..., timeout=0)` → immediate `TimeoutError`.

- Default: 180s (→ 360s max execution). Too short for 32B model under load.
- **Set `LLM_TIMEOUT=1800`** (30 min → 60 min max execution) in `.env`.

### 3. `EMBEDDING_TIMEOUT` — embedding worker timeout
Same pattern as `LLM_TIMEOUT` but for the BGE-M3 embedding queue.

- Default: 30s (→ 60s max execution).
- **Set `EMBEDDING_TIMEOUT=300`** (5 min → 10 min max execution) in `.env`.

### Summary table
| Env var | Controls | Safe value for 3090 |
|---|---|---|
| `TIMEOUT` | httpx read timeout | `0` (infinite) |
| `LLM_TIMEOUT` | Qwen worker timeout | `1800` (30 min) |
| `EMBEDDING_TIMEOUT` | BGE-M3 worker timeout | `300` (5 min) |

---

## BGE-M3 NaN Embeddings — Ollama Flash-Attention Bug

**Problem:** During LightRAG's merging stage (post entity extraction), Ollama
returns HTTP 500 with `failed to encode response: json: unsupported value: NaN`
when LightRAG embeds entity+description pairs via BGE-M3. LightRAG retries 3×,
fails, and marks the document as `failed` — even though extraction succeeded.

**Root cause** ([ollama#13572](https://github.com/ollama/ollama/issues/13572)):
- Ollama v0.13.5 added `"bert"` to the auto-flash-attention list in `fs/ggml/ggml.go`.
- BGE-M3 is BERT-based, so flash attention is silently enabled.
- `llama.cpp/src/llama-graph.cpp:1431-1437` casts K/V tensors F32→F16 before
  `ggml_flash_attn_ext`. F16 max is ~65504; longer/denser inputs overflow to
  Inf → softmax → **NaN**.
- Bug introduced in **v0.13.5**, still present in **0.21.x**.

**Why merging triggers it but extraction doesn't:**
- Extraction embeds short chunks (stays under the overflow threshold).
- Merging embeds `entity_name + "\n" + merged_description` — hundreds to
  thousands of chars, F16 overflow fires.
- Same reason `curl -d '{"input":"Confidentiality"}'` works (short input) but
  the same entity fails inside LightRAG (long description concatenated).

**FIX (confirmed working by 6+ Ollama users):**
Set on the Windows Ollama host:
```
setx OLLAMA_FLASH_ATTENTION false
# then kill + restart ollama.exe so it picks up the env var
```
This disables flash attention globally on the Ollama process. Cost is ~30%
extra VRAM on non-embedding models, which a 24 GB 3090 has headroom for with
Qwen2.5-32B Q4_K_M.

**Things that did NOT fix it** (ruled out experimentally):
- Upgrading Ollama 0.17.7 → 0.21.2 (bug is in llama.cpp path, not version-specific)
- `MAX_ASYNC=1` (serial document processing) — NaN still hit
- `EMBEDDING_FUNC_MAX_ASYNC=2` (lower embed concurrency) — NaN still hit
- Earlier theory of "GPU contention between Qwen + BGE-M3" was WRONG; the NaN
  is purely an F16 overflow in the flash-attn path, regardless of concurrency.

**Alternative workarounds (not applied, documented for reference):**
1. Switch to a non-Ollama embedding backend (HuggingFace TEI or Infinity server) —
   LightRAG maintainer `danielaskdd` explicitly recommends vLLM/SGLang for production.
2. Client-side input truncation patch to `lightrag/llm/ollama.py` `ollama_embed()` —
   truncate inputs progressively (2000→1000→500→200 chars) with placeholder
   fallback ([LightRAG#1870](https://github.com/HKUDS/LightRAG/issues/1870),
   upstream fix in [LightRAG#2916](https://github.com/HKUDS/LightRAG/pull/2916)).
3. Switch to `multilingual-e5-large` via Ollama — same 1024-dim so no schema
   rebuild, same BERT flash-attn caveat so still needs `OLLAMA_FLASH_ATTENTION=false`.

**Affected env vars (now safe to leave at defaults):**
- `MAX_ASYNC` — document-level concurrency. Can raise back to 2+ once flash-attn is off.
- `EMBEDDING_FUNC_MAX_ASYNC` — per-doc embed concurrency. Can raise back to default 8.

---

## Ingestion Workflow

### Re-ingestion after failure
LightRAG persists document state to `data/rag_storage/`. After a failure:
1. `POST /documents/reprocess_failed` — re-queues all failed docs.
2. Extraction results are cached (`LLM cache for extraction: True` at startup),
   so only the failed stage re-runs, not the full extraction.
3. Check per-doc errors via `GET /documents` (not `/documents/status_counts` —
   the latter only gives totals).

### `ollama list` CLI shows stale/wrong model list
Use `curl localhost:11434/api/tags` for the authoritative model list.

### Pipeline status vs document status
- `GET /documents/status_counts` — totals only, fast for polling.
- `GET /documents` — per-doc breakdown with `error_msg` fields.
- `GET /documents/pipeline_status` — current job name, busy flag, latest message.

---

## GitHub / Git Workflow

### PR auto-close on branch delete
When a PR is merged with `--delete-branch` and another PR's base branch is the
now-deleted branch, GitHub auto-closes the second PR. It does NOT retarget it.

**Fix:** Create a fresh PR from the same branch.

### Squash merge + rebase conflict
If phase/02 was branched from phase/01 and phase/01 was squash-merged, the
phase/02 branch contains the pre-squash commits. Rebasing onto `main` fails with
conflicts because the squash commit is a different object.

**Fix:**
```bash
git rebase --onto origin/main <last-phase-01-commit-hash>
```
Drop the pre-squash commits explicitly; only keep phase/02 work.
