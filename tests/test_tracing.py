"""Unit tests for src/tracing — Langfuse query tracing module.

All Langfuse SDK calls are mocked so these tests run without a live Langfuse
instance and without the ``langfuse`` package installed.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.tracing.config import LangfuseConfig
from src.tracing.tracer import init_tracing, trace_query

# ---------------------------------------------------------------------------
# LangfuseConfig tests
# ---------------------------------------------------------------------------


class TestLangfuseConfig:
    def test_from_env_reads_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.setenv("LANGFUSE_HOST", "http://lf.internal:3000")

        cfg = LangfuseConfig.from_env()

        assert cfg.public_key == "pk-test"
        assert cfg.secret_key == "sk-test"
        assert cfg.host == "http://lf.internal:3000"

    def test_from_env_defaults_when_vars_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_HOST", raising=False)

        cfg = LangfuseConfig.from_env()

        assert cfg.public_key == ""
        assert cfg.secret_key == ""
        assert cfg.host == "http://localhost:3000"

    def test_is_configured_true_when_both_keys_present(self) -> None:
        cfg = LangfuseConfig(public_key="pk", secret_key="sk", host="http://x")
        assert cfg.is_configured is True

    def test_is_configured_false_when_public_key_empty(self) -> None:
        cfg = LangfuseConfig(public_key="", secret_key="sk", host="http://x")
        assert cfg.is_configured is False

    def test_is_configured_false_when_secret_key_empty(self) -> None:
        cfg = LangfuseConfig(public_key="pk", secret_key="", host="http://x")
        assert cfg.is_configured is False

    def test_is_configured_false_when_both_keys_empty(self) -> None:
        cfg = LangfuseConfig(public_key="", secret_key="", host="http://x")
        assert cfg.is_configured is False


# ---------------------------------------------------------------------------
# init_tracing tests
# ---------------------------------------------------------------------------


class TestInitTracing:
    def test_returns_none_when_not_configured(self) -> None:
        cfg = LangfuseConfig(public_key="", secret_key="", host="http://x")
        result = init_tracing(cfg)
        assert result is None

    def test_returns_langfuse_client_when_configured(self) -> None:
        cfg = LangfuseConfig(public_key="pk", secret_key="sk", host="http://lf:3000")

        mock_lf_instance = MagicMock()
        mock_lf_class = MagicMock(return_value=mock_lf_instance)

        with patch.dict("sys.modules", {"langfuse": MagicMock(Langfuse=mock_lf_class)}):
            result = init_tracing(cfg)

        mock_lf_class.assert_called_once_with(
            public_key="pk",
            secret_key="sk",
            host="http://lf:3000",
        )
        assert result is mock_lf_instance


# ---------------------------------------------------------------------------
# trace_query tests
# ---------------------------------------------------------------------------


def _make_mock_client() -> MagicMock:
    """Build a mock Langfuse client with the method chain used by trace_query."""
    mock_generation = MagicMock()

    mock_trace = MagicMock()
    mock_trace.generation.return_value = mock_generation

    mock_client = MagicMock()
    mock_client.trace.return_value = mock_trace

    return mock_client


class TestTraceQueryNoop:
    """When client=None, trace_query must be a silent no-op."""

    def test_noop_yields_dict(self) -> None:
        with trace_query(None, question="What is the MSA?", mode="hybrid") as ctx:
            assert isinstance(ctx, dict)

    def test_noop_does_not_raise(self) -> None:
        with trace_query(None, question="Q", mode="local") as ctx:
            ctx["output"] = "answer"
            ctx["tokens_in"] = 5
            ctx["tokens_out"] = 20
            ctx["num_retrieved"] = 3

    def test_noop_caller_can_still_annotate(self) -> None:
        with trace_query(None, question="Q", mode="naive") as ctx:
            ctx["num_retrieved"] = 7
        # No assertion needed — just must not raise.

    def test_noop_when_exception_raised_inside_context(self) -> None:
        with (
            pytest.raises(ValueError, match="test error"),
            trace_query(None, question="Q", mode="global"),
        ):
            raise ValueError("test error")


class TestTraceQueryWithClient:
    """When a real (mocked) Langfuse client is supplied, verify span shape."""

    def test_span_created_with_correct_name(self) -> None:
        client = _make_mock_client()

        with trace_query(client, question="What is SOW-001?", mode="hybrid") as ctx:
            ctx["output"] = "SOW-001 is worth $50 000."

        client.trace.assert_called_once_with(
            name="lightrag.query",
            input="What is SOW-001?",
        )

    def test_custom_name_propagated(self) -> None:
        client = _make_mock_client()

        with trace_query(
            client,
            question="Q",
            mode="local",
            name="custom.span",
        ) as ctx:
            ctx["output"] = "answer"

        client.trace.assert_called_once_with(name="custom.span", input="Q")

    def test_generation_created_with_mode_metadata(self) -> None:
        client = _make_mock_client()

        with trace_query(client, question="Q", mode="global") as ctx:
            ctx["output"] = "A"

        mock_trace = client.trace.return_value
        mock_trace.generation.assert_called_once()
        call_kwargs = mock_trace.generation.call_args.kwargs
        assert call_kwargs["metadata"]["mode"] == "global"

    def test_latency_ms_is_positive_int(self) -> None:
        client = _make_mock_client()

        with trace_query(client, question="Q", mode="hybrid") as ctx:
            ctx["output"] = "A"

        assert "latency_ms" in ctx
        assert isinstance(ctx["latency_ms"], int)
        assert ctx["latency_ms"] >= 0

    def test_trace_update_carries_expected_metadata_keys(self) -> None:
        client = _make_mock_client()

        with trace_query(client, question="Q", mode="local") as ctx:
            ctx["output"] = "answer text"
            ctx["tokens_in"] = 10
            ctx["tokens_out"] = 25
            ctx["num_retrieved"] = 4
            ctx["rerank_applied"] = True

        mock_trace = client.trace.return_value
        mock_trace.update.assert_called_once()
        metadata = mock_trace.update.call_args.kwargs["metadata"]

        assert metadata["mode"] == "local"
        assert metadata["num_retrieved"] == 4
        assert metadata["rerank_applied"] is True
        assert metadata["tokens_in"] == 10
        assert metadata["tokens_out"] == 25
        assert isinstance(metadata["latency_ms"], int)

    def test_generation_end_called_with_usage(self) -> None:
        client = _make_mock_client()

        with trace_query(client, question="Q", mode="hybrid") as ctx:
            ctx["output"] = "answer"
            ctx["tokens_in"] = 8
            ctx["tokens_out"] = 32

        mock_generation = client.trace.return_value.generation.return_value
        mock_generation.end.assert_called_once()
        end_kwargs = mock_generation.end.call_args.kwargs
        assert end_kwargs["usage"] == {"input": 8, "output": 32}

    def test_flush_called_after_query(self) -> None:
        client = _make_mock_client()

        with trace_query(client, question="Q", mode="naive") as ctx:
            ctx["output"] = "A"

        client.flush.assert_called_once()

    def test_span_ends_even_when_exception_raised(self) -> None:
        """Verify finally-block cleanup runs on exception."""
        client = _make_mock_client()

        with (
            pytest.raises(RuntimeError, match="query failed"),
            trace_query(client, question="Q", mode="hybrid"),
        ):
            raise RuntimeError("query failed")

        # generation.end and flush must still have been called
        mock_generation = client.trace.return_value.generation.return_value
        mock_generation.end.assert_called_once()
        client.flush.assert_called_once()

    def test_default_values_used_when_ctx_not_populated(self) -> None:
        """When the caller doesn't annotate ctx, defaults are sensible."""
        client = _make_mock_client()

        with trace_query(client, question="Q", mode="hybrid"):
            pass  # no ctx annotations

        mock_generation = client.trace.return_value.generation.return_value
        end_kwargs = mock_generation.end.call_args.kwargs
        assert end_kwargs["usage"] == {"input": 0, "output": 0}

        mock_trace = client.trace.return_value
        metadata = mock_trace.update.call_args.kwargs["metadata"]
        assert metadata["num_retrieved"] == 0
        assert metadata["rerank_applied"] is False
