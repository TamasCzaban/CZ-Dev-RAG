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

## BGE-M3 NaN Embeddings Under Concurrent GPU Load

**Problem:** During LightRAG's merging stage, multiple entity/relation names are
embedded concurrently using `EMBEDDING_FUNC_MAX_ASYNC` (default: 8) workers.
On a single 3090 running Qwen2.5-32B and BGE-M3 simultaneously, 8 concurrent
embedding calls cause GPU memory bandwidth contention. BGE-M3 occasionally
produces `NaN` values in its output tensor, and Ollama responds with:
```
HTTP 500: failed to encode response: json: unsupported value: NaN
```
LightRAG retries 3× then marks the document as `failed` during the merging
stage — even though entity extraction succeeded.

**Key insight:** The failure is probabilistic. A single doc may succeed while
another fails. The extraction results are cached, so reprocessing only re-runs
the merging stage (fast, minutes not hours).

**Fix:** Set `EMBEDDING_FUNC_MAX_ASYNC=2` in `.env`. This limits concurrent
BGE-M3 calls to 2, dramatically reducing GPU contention during merging.

**Did NOT fix it:** Upgrading Ollama from 0.17.7 → 0.21.2. The NaN is a
GPU-contention issue, not an Ollama version issue.

**Affected env var:** `EMBEDDING_FUNC_MAX_ASYNC` (LightRAG constant default: 8).

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
