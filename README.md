# CZ-Dev-RAG

> Local, graph-based knowledge base for a two-person software agency. LightRAG + RAG-Anything, RTX 3090, Windows-native Ollama, Tailscale for remote access. Public code, private data.

![status](https://img.shields.io/badge/status-scaffolding-orange) ![license](https://img.shields.io/badge/license-MIT-blue) ![python](https://img.shields.io/badge/python-3.11+-blue)

**Repository state:** scaffolding only. Implementation is tracked as GSD phases — see [`ROADMAP.md`](./ROADMAP.md).

## What this is

An internal, locally-hosted knowledge base for CZ Dev (czaban.dev). Client contracts, meeting notes, and SOWs are ingested into a LightRAG graph on an RTX 3090 running Windows 11 with native Ollama. Queries run through the LightRAG web UI or via a dedicated MCP server that exposes the KB as a tool to Claude Code / Cursor. Tamas and Zsombor access the same KB from anywhere over Tailscale.

The repo is public and doubles as a portfolio artifact for AI/ML Engineer job applications. Client data is never committed; a synthetic `examples/demo-corpus/` makes the repo runnable by anyone cloning it.

## Architecture

```mermaid
flowchart LR
    Docs[data/input/{client_slug}/] --> MinerU
    Demo[examples/demo-corpus/] --> MinerU
    MinerU[MinerU parser<br/>CPU] --> LightRAG
    subgraph Host[Windows 11 + RTX 3090]
        Ollama[Ollama native<br/>BGE-M3 + Qwen2.5-32B]
    end
    subgraph Docker[Docker Desktop]
        LightRAG[LightRAG server<br/>+ RAG-Anything]
        Reranker[BGE-reranker-v2-m3]
        Langfuse[Langfuse<br/>tracing]
        MCP[MCP server<br/>query_kb + list_documents]
    end
    LightRAG -->|extract + embed| Ollama
    LightRAG --> Reranker
    LightRAG --> Langfuse
    MCP --> LightRAG
    LightRAG --> Storage[(nano-vectordb<br/>+ file graph)]
    Tailscale[Tailscale<br/>tamas + zsombor devices] --> LightRAG
    Tailscale --> MCP
```

## Quickstart (recruiter-friendly)

> Target: `docker compose up` on a fresh Windows 11 machine, working demo in 15 minutes.

**Prerequisites:**
1. [Ollama for Windows](https://ollama.com/download/windows) — installed and running
2. [Docker Desktop](https://www.docker.com/products/docker-desktop/) — installed and running
3. NVIDIA driver ≥550 (for Ollama GPU; Docker services run CPU)

**Setup:** _coming in phase 01_

```bash
git clone https://github.com/TamasCzaban/CZ-Dev-RAG
cd CZ-Dev-RAG
cp .env.example .env
ollama pull bge-m3
ollama pull qwen2.5:32b-instruct-q4_K_M
docker compose up -d
# Open http://localhost:9621
# Upload files from examples/demo-corpus/
# Ask: "What are the payment terms in the AcmeCo MSA?"
```

## Evaluation results

_Eval harness lands in phase 05. Results table auto-populated here._

```
| Mode    | Faithfulness | Answer Relevance | Context Precision |
|---------|--------------|------------------|-------------------|
| naive   | —            | —                | —                 |
| local   | —            | —                | —                 |
| global  | —            | —                | —                 |
| hybrid  | —            | —                | —                 |
```

## MCP server

Expose the KB to Claude Code:

```json
{
  "mcpServers": {
    "cz-dev-kb": {
      "command": "docker",
      "args": ["exec", "-i", "cz-dev-rag-mcp", "python", "/app/server.py"]
    }
  }
}
```

_Details in phase 06._

## Documentation

- [`ROADMAP.md`](./ROADMAP.md) — implementation phases
- [`STATE.md`](./STATE.md) — current phase + status
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — data flow + component boundaries
- [`docs/DECISIONS.md`](./docs/DECISIONS.md) — ADRs explaining tech choices

## Built with

[LightRAG](https://github.com/HKUDS/LightRAG) · [RAG-Anything](https://github.com/HKUDS/RAG-Anything) · [Ollama](https://ollama.com) · [Langfuse](https://langfuse.com) · [Ragas](https://docs.ragas.io) · [MinerU](https://github.com/opendatalab/MinerU) · [Tailscale](https://tailscale.com)

## License

MIT — see [LICENSE](./LICENSE).

---

Built by [Tamas Czaban](https://czaban.dev) · CZ Dev software agency.
