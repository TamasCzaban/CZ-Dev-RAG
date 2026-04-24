import os
from dataclasses import dataclass


@dataclass
class LangfuseConfig:
    """Langfuse connection configuration, read from environment variables."""

    public_key: str
    secret_key: str
    host: str

    @classmethod
    def from_env(cls) -> "LangfuseConfig":
        """Construct config from environment variables.

        Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST.
        If credentials are not set the tracing module operates in no-op mode.
        """
        return cls(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY", ""),
            host=os.environ.get("LANGFUSE_HOST", "http://localhost:3000"),
        )

    @property
    def is_configured(self) -> bool:
        """Return True when both API keys are non-empty."""
        return bool(self.public_key and self.secret_key)
