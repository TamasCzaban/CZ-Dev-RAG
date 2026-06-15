# Phase 11 — Compose profile for client-only MCP

## Issue
[#27](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/27)

## Branch
`phase/11-compose-client-mcp-profile`

## Goal
Allow Zsombor to run the MCP server without spinning up the full local stack (lightrag, reranker, langfuse). Currently `mcp` has `depends_on: lightrag: condition: service_healthy`, which forces lightrag to start even with `--no-deps`.

## Acceptance Criteria
1. `docker compose up mcp --no-deps -d` does NOT start lightrag, reranker, or langfuse-* containers.
2. OR: `docker compose --profile client up mcp -d` does the same.
3. `docker compose logs mcp` shows MCP server waiting (no crash) when `LIGHTRAG_HOST` points to an unreachable URL.

## Analysis
The `mcp` service in `docker-compose.yml`:
- Has `depends_on: lightrag: condition: service_healthy` — this causes the full stack to start even with `--no-deps` because Docker requires healthy dependencies before the service starts.
- `LIGHTRAG_HOST` is hardcoded to `http://lightrag:9621` — this works on Tamas's box but breaks on Zsombor's.

## Implementation Plan

### Wave 1 — Add `profiles: [client]` to `mcp` service
- Add `profiles: [client]` to the `mcp` service block.
- Remove (or make conditional) `depends_on: lightrag` — when running in client profile, there is no local lightrag.
- Change `LIGHTRAG_HOST` default to use env var `${LIGHTRAG_HOST:-http://lightrag:9621}` so Zsombor can override it via `.env`.
- Add a comment block explaining client vs full-stack usage.

### Wave 2 — Update `.env.example`
- Add `LIGHTRAG_HOST=http://lightrag:9621` with a comment: "Override for client mode — set to Tailscale host, e.g. http://100.x.y.z:9621"

### Wave 3 — Update ROADMAP.md phase status
- Mark Phase 11 as `DONE` in ROADMAP.md.

## Testing
Integration smoke (manual): `docker compose --profile client up mcp -d` — only `mcp` container starts.
