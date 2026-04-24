"""Langfuse tracing helpers for the LightRAG query pipeline.

Design note: LightRAG runs as an HTTP service; we cannot hook into its
internals. Tracing therefore wraps the *caller's* HTTP call so every query
emits a Langfuse span with latency, token counts, mode, and retrieval shape.

When LANGFUSE_PUBLIC_KEY is empty, ``init_tracing`` returns None and
``trace_query`` is a no-op context manager — no exceptions, no side-effects.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from src.tracing.config import LangfuseConfig

if TYPE_CHECKING:
    import langfuse as langfuse_module


def init_tracing(config: LangfuseConfig) -> langfuse_module.Langfuse | None:
    """Initialise a Langfuse client from *config*.

    Returns ``None`` when credentials are not configured so that callers can
    treat ``None`` as "no-op mode" without any special-casing at the call site.
    """
    if not config.is_configured:
        return None

    import langfuse  # local import so missing package only fails when used

    return langfuse.Langfuse(
        public_key=config.public_key,
        secret_key=config.secret_key,
        host=config.host,
    )


@contextmanager
def trace_query(
    client: langfuse_module.Langfuse | None,
    *,
    question: str,
    mode: str,
    name: str = "lightrag.query",
) -> Generator[dict[str, Any], None, None]:
    """Context manager that wraps a LightRAG HTTP query with a Langfuse span.

    Yields a mutable *ctx* dict that the caller populates with results::

        with trace_query(lf_client, question=q, mode="hybrid") as ctx:
            result = lightrag_http_query(q, mode="hybrid")
            ctx["output"] = result["answer"]
            ctx["tokens_in"] = result.get("prompt_tokens", 0)
            ctx["tokens_out"] = result.get("completion_tokens", 0)
            ctx["num_retrieved"] = len(result.get("sources", []))
            ctx["rerank_applied"] = result.get("reranked", False)

    When *client* is ``None`` (no-op mode), yields an empty dict and does
    nothing else. No exceptions are raised in no-op mode.

    The span is always closed in the ``finally`` block, so Langfuse receives
    the span even if the query raises an exception.

    Recorded fields
    ---------------
    ``latency_ms``       Wall-clock time for the query in milliseconds (int).
    ``tokens_in``        Prompt token count (caller-supplied, default 0).
    ``tokens_out``       Completion token count (caller-supplied, default 0).
    ``mode``             LightRAG retrieval mode (e.g. "hybrid").
    ``num_retrieved``    Number of source chunks returned (caller-supplied).
    ``rerank_applied``   Whether the BGE reranker was applied (bool).
    """
    if client is None:
        # No-op mode: yield an empty dict and exit cleanly.
        ctx: dict[str, Any] = {}
        yield ctx
        return

    # --- Langfuse tracing path ---
    ctx = {
        "output": "",
        "tokens_in": 0,
        "tokens_out": 0,
        "num_retrieved": 0,
        "rerank_applied": False,
    }

    trace = client.trace(name=name, input=question)
    generation = trace.generation(
        name="query",
        input=question,
        model="qwen2.5:32b-instruct-q4_K_M",
        metadata={"mode": mode},
    )

    start_ms = time.monotonic() * 1_000
    try:
        yield ctx
    finally:
        latency_ms = int(time.monotonic() * 1_000 - start_ms)
        ctx["latency_ms"] = latency_ms

        generation.end(
            output=ctx.get("output", ""),
            usage={
                "input": ctx.get("tokens_in", 0),
                "output": ctx.get("tokens_out", 0),
            },
        )
        trace.update(
            output=ctx.get("output", ""),
            metadata={
                "mode": mode,
                "latency_ms": latency_ms,
                "num_retrieved": ctx.get("num_retrieved", 0),
                "rerank_applied": ctx.get("rerank_applied", False),
                "tokens_in": ctx.get("tokens_in", 0),
                "tokens_out": ctx.get("tokens_out", 0),
            },
        )
        client.flush()
