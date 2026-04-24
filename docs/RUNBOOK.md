# CZ-Dev-RAG - Operational Runbook

Target audience: Tamas (host operator) and Zsombor (remote user). Every command is real and validated against the actual stack.

---

## Host prerequisites (one time, Tamas machine)

**OS:** Windows 11 Pro. **GPU:** NVIDIA driver >= 550.

```powershell
nvidia-smi
```

**Docker Desktop for Windows** with WSL2 backend enabled. Verify:

```powershell
docker version
docker compose version
```

**Ollama for Windows** - download from [ollama.com/download/windows](https://ollama.com/download/windows), run the installer. Installs itself as a Windows service on boot.

```powershell
ollama list
```

### CRITICAL: disable WSL Ollama if it exists

Docker Desktop uses WSL2. If Ollama is also installed inside WSL and its systemd service is enabled, `wslrelay.exe` bridges WSL 127.0.0.1:11434 to the Windows host. `host.docker.internal` inside Docker resolves to 127.0.0.1 first - hitting the WSL Ollama, not the Windows one - causing `model not found` errors even though the correct models exist in Windows Ollama.

```bash
wsl -- sudo systemctl disable --now ollama
wsl --shutdown
```

Verify only one listener owns 11434:

```powershell
netstat -an | findstr 11434
```

### CRITICAL: disable flash attention before first run

BGE-M3 returns NaN embeddings when Ollama flash attention is enabled (upstream bug: github.com/ollama/ollama/issues/13572). Set in Windows Machine environment variables before starting Ollama:

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "false", "Machine")
Stop-Service -Name "Ollama" -Force
Start-Service -Name "Ollama"
```

Verify:

```powershell
[System.Environment]::GetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "Machine")
# Must print: false
```

See LEARNINGS.md for full root-cause analysis.

---

## Model pulls (one-time, ~20 GB)

```bash
ollama pull bge-m3
ollama pull qwen2.5:32b-instruct-q4_K_M
ollama list
```

Expected sizes: BGE-M3 ~1.5 GB, Qwen2.5-32B Q4_K_M ~19 GB. Allow 15-30 min on a fast connection.

---

## Stack startup

```bash
git clone https://github.com/TamasCzaban/CZ-Dev-RAG
cd CZ-Dev-RAG
cp .env.example .env
```

Edit `.env` before first boot - at minimum:

```
LANGFUSE_DB_PASSWORD=<strong-password>
LANGFUSE_NEXTAUTH_SECRET=<48-char-random>
LANGFUSE_SALT=<48-char-random>
```

Generate secrets: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

```bash
docker compose up -d
docker compose ps   # wait until lightrag + langfuse-web show (healthy)
```

Services on host:

| Service         | URL                    | Notes                         |
|-----------------|------------------------|-------------------------------|
| LightRAG UI+API | http://localhost:9621  | Upload, query, graph explorer |
| Langfuse        | http://localhost:3000  | Create org on first visit     |
| BGE-reranker    | internal (:7997)       | Not exposed on host           |
| MCP server      | Docker stdio           | Via docker compose exec       |

After creating a Langfuse project, add its keys to `.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`):

```bash
docker compose restart langfuse-web
```

---

## Tailscale setup

### Tamas Windows host

1. Install Tailscale for Windows from tailscale.com/download/windows.
2. `tailscale up` - authenticates via browser.
3. `tailscale ip -4` - note the tailnet IP.
4. In the Tailscale admin console (login.tailscale.com/admin/acls), restrict ports 9621 and 9622 to tailnet members only.

Ports 9621 and 3000 do NOT need Windows Firewall inbound rules for Tailscale access - WireGuard tunnels directly.

### Zsombor machine (any OS)

```bash
tailscale up --authkey <short-lived-or-reusable-key>
```

Generate auth key in Tailscale admin console: Settings > Keys > Generate auth key. Use a reusable key with 1-day expiry for a new machine.

Verify connectivity:

```bash
curl http://<tamas-tailnet-ip>:9621/health
```

Expected: 200 response with status ok.

### Auth key rotation

```bash
tailscale up --authkey <new-key>
```

---

## Ingesting documents

```bash
# Demo corpus - first-time smoke test
python scripts/ingest.py examples/demo-corpus/ --lightrag-url http://localhost:9621

# Client documents - recursive (processes .md .txt .pdf)
python scripts/ingest.py data/input/client-slug/ --recursive

# Dry run - list files without posting
python scripts/ingest.py data/input/client-slug/ --dry-run

# From Zsombor machine over Tailscale
python scripts/ingest.py examples/demo-corpus/ --lightrag-url http://<tamas-tailnet-ip>:9621
```

Demo corpus (5 docs) ingests in ~3-5 min on the 3090. Expect high VRAM usage during ingest.

---

## Backup schedule

### Set env vars (Windows host, Machine scope)

```powershell
[System.Environment]::SetEnvironmentVariable("B2_ACCOUNT_ID",     "<your-b2-account-id>",       "Machine")
[System.Environment]::SetEnvironmentVariable("B2_ACCOUNT_KEY",    "<your-b2-app-key>",          "Machine")
[System.Environment]::SetEnvironmentVariable("RESTIC_PASSWORD",   "<strong-passphrase>",        "Machine")
[System.Environment]::SetEnvironmentVariable("RESTIC_REPOSITORY", "b2:bucket-name:/cz-dev-rag", "Machine")
```

Use a Backblaze B2 application key scoped to the bucket - never the master key.

### One-time repo init (first time only)

```bash
restic init
```

### Manual backup test

```bash
bash scripts/backup.sh
restic snapshots   # should show one snapshot tagged cz-dev-rag
```

The script backs up `data/` (rag_storage + input), keeps 7 daily and 4 weekly snapshots, prunes automatically.

### Schedule via Windows Task Scheduler (daily at 03:00)

```powershell
schtasks /create /tn "CZ-Dev-RAG Backup" /tr "bash C:\Users\Toma\projects\CZ-Dev-RAG\scripts\backup.sh" /sc daily /st 03:00 /ru SYSTEM /f
```

Verify and trigger:

```powershell
schtasks /query /tn "CZ-Dev-RAG Backup"
schtasks /run /tn "CZ-Dev-RAG Backup"
# wait ~30s then:
restic snapshots
```

---

## Restore drill

Execute before marking phase 09 complete. The runbook acceptance criterion is a real restore on the host.

```bash
# 1. Stop LightRAG so it is not writing during restore
docker compose stop lightrag

# 2. Delete the live storage
rm -rf data/rag_storage/

# 3. List available snapshots (load env first — restic needs B2 creds)
set -a && source .env && set +a
restic snapshots

# 4. Restore — use --target / so restic writes back to the original absolute path.
#    Do NOT use --target <repo-root>: restic would nest the full Windows path
#    under the target, producing data/ at <repo-root>/C/Users/.../data/.
set -a && source .env && set +a
restic restore latest --target /

# 5. Restart LightRAG
docker compose start lightrag

# 6. Wait for healthy, then sanity query
docker compose ps

curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the payment terms in the AcmeCo MSA?", "mode": "hybrid"}'
```

> **Windows note:** if `restic` is not on PATH (winget install, fresh shell), use the full
> exe path from `scripts/backup.sh` (the `RESTIC_WINGET` fallback variable shows the location).

Expected: non-empty JSON with an `answer` field referencing the AcmeCo MSA.

Sign-off: record snapshot ID, restore time, and confirm the sanity query returned a correct answer. This is the acceptance criterion for phase 09.

---

## Routine maintenance

### Update Ollama

Download new installer from ollama.com/download/windows, run it. Installer updates in place; service restarts automatically.

```bash
ollama --version
ollama list
```

### Update LightRAG

```bash
docker compose pull lightrag
docker compose up -d lightrag
docker compose ps
```

### Update all containers

```bash
docker compose pull
docker compose up -d
```

### Monthly disk check

```bash
du -sh data/
du -sh data/rag_storage/
```

Alert if rag_storage exceeds 10 GB - consider archiving old client data.

### Langfuse Postgres vacuum

```bash
docker compose exec langfuse-postgres psql -U langfuse -c "VACUUM ANALYZE;"
```

Run monthly or after bulk deletions. The `langfuse_data` named volume is NOT under `data/` and is not covered by `backup.sh` - back it up separately if trace history matters.

---

## Troubleshooting

### LightRAG cannot reach Ollama

```bash
docker compose exec lightrag curl http://host.docker.internal:11434/api/tags
```

If this fails: confirm ollama.exe is running (`ollama list` from PowerShell). Check WSL Ollama is disabled. `host.docker.internal` is set via `extra_hosts` in docker-compose.yml by Docker Desktop.

### BGE-M3 NaN embeddings (HTTP 500 on ingest)

Error: `failed to encode response: json: unsupported value: NaN`

Fix:

1. Confirm `OLLAMA_FLASH_ATTENTION=false` is a Machine-level Windows env var.
2. `Stop-Service Ollama -Force; Start-Service Ollama`
3. Delete `data/rag_storage/` and re-ingest from scratch (corrupt embeddings cannot be fixed in place).

See LEARNINGS.md for full root cause.

### Langfuse Postgres will not start

```bash
docker compose logs langfuse-postgres
```

To reset (destroys all Langfuse trace history):

```bash
docker compose down
docker volume rm cz-dev-rag_langfuse_data
docker compose up -d
```

### LightRAG ingestion times out

Symptom: `asyncio.TimeoutError` in `docker compose logs lightrag`.

Check `.env`: `LLM_TIMEOUT=1800` (must not be 0), `EMBEDDING_TIMEOUT=300`, `MAX_ASYNC=1` for fresh setup. See LEARNINGS.md timeout section.

### Reranker OOM

Reranker runs on CPU by design (VRAM is fully allocated to Qwen2.5-32B + BGE-M3). If it crashes with OOM, reduce `RERANK_TOP_K` in `.env` (default: 20):

```bash
docker compose restart reranker
```

### MCP server not connecting

```bash
docker compose ps mcp
docker compose logs mcp
```

MCP depends on lightrag being healthy - fix LightRAG first, then `docker compose restart mcp`. MCP communicates via stdio; confirm `cwd` in `claude_desktop_config.json` points to the actual clone location.