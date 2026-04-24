# CZ-Dev-RAG Operational Scripts

## `ingest.py` — Bulk document ingestion

Posts `.md`, `.txt`, and `.pdf` files from a local folder to the LightRAG HTTP API.

**When to run:** after dropping new client documents into `data/input/<client_slug>/`.

```bash
# Ingest everything under data/input/acmeco/ (recursive, default)
python scripts/ingest.py data/input/acmeco/

# Preview without sending anything
python scripts/ingest.py data/input/acmeco/ --dry-run

# Flat folder only (skip subdirectories)
python scripts/ingest.py data/input/acmeco/ --no-recursive

# Override LightRAG URL (default: $LIGHTRAG_HOST or http://localhost:9621)
python scripts/ingest.py data/input/acmeco/ --lightrag-url http://100.x.x.x:9621
```

Exit code is non-zero if any file fails. All failures are listed in the summary.

---

## `delete_by_source.py` — Delete a document by ID

Calls `DELETE /documents/{doc_id}` on the LightRAG API. LightRAG assigns document IDs
during ingestion; find them via the LightRAG web UI at `http://localhost:9621`.

**When to run:** when a client relationship ends, a contract is superseded, or a document
was ingested by mistake.

```bash
# Interactive confirmation (recommended)
python scripts/delete_by_source.py <doc_id>

# Skip confirmation (for scripting)
python scripts/delete_by_source.py <doc_id> --yes
```

Exit code is non-zero on HTTP error or when the user aborts.

---

## `backup.sh` — Restic backup to Backblaze B2

Backs up the entire `data/` directory (LightRAG graph + vector store + raw input files)
to a Backblaze B2 bucket using restic. Runs `forget` immediately after with a
7-daily / 4-weekly retention policy.

**When to run:** daily via Windows Task Scheduler.

**Prerequisites:**
- `restic` installed and on PATH (`winget install restic` or `choco install restic`)
- A Backblaze B2 bucket created at [backblaze.com](https://www.backblaze.com)
- The following environment variables set (add to `.env` or Task Scheduler env):

```
B2_ACCOUNT_ID=<your-b2-key-id>
B2_ACCOUNT_KEY=<your-b2-application-key>
RESTIC_PASSWORD=<strong-passphrase>
RESTIC_REPOSITORY=b2:<bucket-name>:/cz-dev-rag
```

**First-time init** (one-off, creates the repo):
```bash
restic init
```

**Manual run:**
```bash
source .env  # or set env vars however you prefer
bash scripts/backup.sh
```

### Scheduling with Windows Task Scheduler

Run once to register a daily 2 AM task (replace `C:\path\to\CZ-Dev-RAG` with your actual path):

```powershell
schtasks /Create /SC DAILY /TN "CZ-Dev-RAG Backup" /TR "bash C:\path\to\CZ-Dev-RAG\scripts\backup.sh" /ST 02:00 /RU SYSTEM /F
```

> Note: Task Scheduler runs as SYSTEM by default; store env vars in the system environment
> (`System Properties → Advanced → Environment Variables → System variables`) rather than
> in `.env` so the scheduler task can read them.
