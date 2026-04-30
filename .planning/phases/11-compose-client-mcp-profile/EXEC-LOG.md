# Phase 11 — Execution Log

## Wave 1 — docker-compose.yml changes

**Problem:** `mcp` service had `depends_on: lightrag: condition: service_healthy`. With `--no-deps`, Docker would skip starting lightrag but the healthcheck dependency condition could still prevent start or cause unexpected behavior. The `profiles: [client]` approach is the canonical Docker Compose solution.

**Changes:**
- Removed `depends_on: lightrag` from `mcp` service (dependency no longer needed — MCP fails fast at query time, not boot time).
- Added `profiles: [client]` to `mcp` service — excludes it from default `docker compose up`, includes it only when `--profile client` is passed.
- Changed `LIGHTRAG_HOST` from hardcoded `http://lightrag:9621` to `${LIGHTRAG_HOST:-http://lightrag:9621}` — env-var overridable for Zsombor's Tailscale setup.
- Added detailed comment block explaining both usage modes.

**Verification:**
- `docker compose config --services` → `[langfuse-postgres, langfuse-web, lightrag, reranker]` (mcp excluded from default)
- `docker compose --profile client config --services` → `[..., mcp, ...]` (mcp included with profile)
- `docker compose config --quiet` → VALID (no syntax errors)

## Wave 2 — .env.example

Added `LIGHTRAG_HOST` variable with documentation pointing Zsombor to override it with the Tailscale peer address for client mode.

## Wave 3 — ROADMAP.md

Updated Phase 11 status from `NOT STARTED` to `DONE`.

## Files changed
- `docker-compose.yml` — mcp service: add profile, remove depends_on, env-var LIGHTRAG_HOST, updated comment
- `.env.example` — add LIGHTRAG_HOST with client-mode documentation
- `ROADMAP.md` — Phase 11 status → DONE
- `.planning/phases/11-compose-client-mcp-profile/PLAN.md` — planning artifact
- `.planning/phases/11-compose-client-mcp-profile/EXEC-LOG.md` — this file
