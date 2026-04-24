"""Delete a document from the CZ-Dev-RAG LightRAG knowledge base by document ID."""

from __future__ import annotations

import sys
from typing import Annotated

import httpx
import typer

app = typer.Typer(help="Delete a document from the LightRAG knowledge base by document ID.")

DEFAULT_LIGHTRAG_URL = "http://localhost:9621"


def delete_document(
    doc_id: str,
    *,
    yes: bool,
    lightrag_url: str,
) -> int:
    """Core delete logic — returns exit code (0 = deleted, 1 = aborted/error)."""
    if not yes:
        confirm = typer.prompt(
            f"Delete document '{doc_id}'? [y/N]",
            default="N",
            show_default=False,
        )
        if confirm.strip().lower() != "y":
            typer.echo("Aborted.")
            return 1

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{lightrag_url}/documents/{doc_id}",
                timeout=30.0,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        typer.echo(
            f"Error: HTTP {exc.response.status_code} — {exc.response.text[:200]}",
            err=True,
        )
        return 1
    except httpx.RequestError as exc:
        typer.echo(f"Error: Request failed — {exc}", err=True)
        return 1

    typer.echo(f"Deleted {doc_id}")
    return 0


@app.command()
def main(
    doc_id: Annotated[str, typer.Argument(help="Document ID to delete.")],
    yes: Annotated[
        bool,
        typer.Option("--yes/--no-yes", "-y", help="Skip confirmation prompt."),
    ] = False,
    lightrag_url: Annotated[
        str,
        typer.Option(
            "--lightrag-url",
            envvar="LIGHTRAG_HOST",
            help="LightRAG HTTP API base URL.",
        ),
    ] = DEFAULT_LIGHTRAG_URL,
) -> None:
    """Delete a document from the LightRAG knowledge base."""
    exit_code = delete_document(doc_id, yes=yes, lightrag_url=lightrag_url)
    sys.exit(exit_code)


if __name__ == "__main__":
    app()
