from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

import httpx
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.mcp_server.lightrag_client import LightRAGClient

LIGHTRAG_HOST = os.environ.get("LIGHTRAG_HOST", "http://lightrag:9621")
VALID_MODES = {"naive", "local", "global", "hybrid"}
server: Server = Server("cz-dev-rag")


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_kb",
            description="Query the CZ Dev knowledge base using LightRAG.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to ask."},
                    "mode": {
                        "type": "string",
                        "enum": list(VALID_MODES),
                        "default": "hybrid",
                        "description": "Retrieval mode: naive | local | global | hybrid.",
                    },
                },
                "required": ["question"],
            },
        ),
        types.Tool(
            name="list_documents",
            description="List all documents ingested into the knowledge base.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    # TODO(phase-10): add Langfuse span here
    client = LightRAGClient(LIGHTRAG_HOST)
    try:
        if name == "query_kb":
            question: str = arguments["question"]
            mode: str = arguments.get("mode", "hybrid")
            if mode not in VALID_MODES:
                return [types.TextContent(type="text", text=json.dumps(
                    {"error": f"Invalid mode '{mode}'. Choose from {sorted(VALID_MODES)}."}
                ))]
            t0 = time.monotonic()
            raw = await client.query(question, mode)
            latency_ms = int((time.monotonic() - t0) * 1000)
            answer = raw.get("response") or raw.get("answer") or str(raw)
            result: dict[str, Any] = {
                "answer": answer, "sources": raw.get("sources", []), "latency_ms": latency_ms,
            }
            return [types.TextContent(type="text", text=json.dumps(result))]

        if name == "list_documents":
            docs = await client.list_documents()
            normalized = [
                {
                    "doc_id": d.get("id", d.get("doc_id", "")),
                    "source_path": d.get("source_path", d.get("file_path", "")),
                    "ingested_at": d.get("ingested_at", d.get("created_at", "")),
                    "chunk_count": d.get("chunk_count", 0),
                }
                for d in docs
            ]
            return [types.TextContent(type="text", text=json.dumps(normalized))]

        return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except httpx.ConnectError as exc:
        return [types.TextContent(type="text", text=json.dumps(
            {"error": f"Cannot reach LightRAG at {LIGHTRAG_HOST}: {exc}"}
        ))]
    except Exception as exc:
        return [types.TextContent(type="text", text=json.dumps({"error": str(exc)}))]
    finally:
        await client.close()


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
