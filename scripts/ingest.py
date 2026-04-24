"""Bulk ingestion script for CZ-Dev-RAG.

Posts .md, .txt, and .pdf files from a folder to the LightRAG HTTP API.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import httpx
import typer

try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    _RICH = True
    _console = Console()
except ImportError:
    _RICH = False
    _console = None  # type: ignore[assignment]

app = typer.Typer(help="Ingest documents into the CZ-Dev-RAG LightRAG knowledge base.")

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
DEFAULT_LIGHTRAG_URL = "http://localhost:9621"


def _collect_files(folder: Path, *, recursive: bool) -> list[Path]:
    """Return all supported files under *folder*, ordered by path."""
    if recursive:
        files = [
            p
            for p in folder.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    else:
        files = [
            p
            for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    return sorted(files)


def _post_document(
    client: httpx.Client,
    url: str,
    file_path: Path,
    folder: Path,
) -> tuple[bool, str]:
    """POST a single document to the LightRAG API.

    Returns (success, error_message).
    """
    relative = file_path.relative_to(folder)
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return False, f"Cannot read {file_path}: {exc}"

    payload = {
        "text": text,
        "metadata": {
            "source": str(relative).replace("\\", "/"),
            "filename": file_path.name,
        },
    }
    try:
        response = client.post(f"{url}/documents/text", json=payload, timeout=120.0)
        response.raise_for_status()
        return True, ""
    except httpx.HTTPStatusError as exc:
        return False, f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
    except httpx.RequestError as exc:
        return False, f"Request error: {exc}"


def ingest_folder(
    folder: Path,
    *,
    recursive: bool,
    dry_run: bool,
    lightrag_url: str,
) -> int:
    """Core ingestion logic — returns exit code (0 = all ok, 1 = any failure)."""
    if not folder.is_dir():
        typer.echo(f"Error: '{folder}' is not a directory.", err=True)
        return 1

    files = _collect_files(folder, recursive=recursive)
    if not files:
        typer.echo("No supported files found (.md, .txt, .pdf).")
        return 0

    if dry_run:
        typer.echo(f"Dry run — {len(files)} file(s) would be ingested:")
        for f in files:
            typer.echo(f"  {f.relative_to(folder)}")
        return 0

    succeeded = 0
    failed = 0
    errors: list[str] = []

    if _RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=_console,
        ) as progress:
            task = progress.add_task("Ingesting", total=len(files))
            with httpx.Client() as client:
                for file_path in files:
                    progress.update(task, description=f"[cyan]{file_path.name}[/cyan]")
                    ok, err = _post_document(client, lightrag_url, file_path, folder)
                    if ok:
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"{file_path.name}: {err}")
                    progress.advance(task)
    else:
        with httpx.Client() as client:
            for i, file_path in enumerate(files, 1):
                print(f"[{i}/{len(files)}] {file_path.name} ... ", end="", flush=True)
                ok, err = _post_document(client, lightrag_url, file_path, folder)
                if ok:
                    succeeded += 1
                    print("OK")
                else:
                    failed += 1
                    errors.append(f"{file_path.name}: {err}")
                    print(f"FAILED — {err}")

    typer.echo(f"\nSummary: {succeeded} succeeded, {failed} failed.")
    for err in errors:
        typer.echo(f"  ERROR: {err}", err=True)

    return 0 if failed == 0 else 1


@app.command()
def main(
    folder: Annotated[Path, typer.Argument(help="Folder containing documents to ingest.")],
    recursive: Annotated[
        bool,
        typer.Option("--recursive/--no-recursive", help="Recurse into subdirectories."),
    ] = True,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--no-dry-run", help="Print files without ingesting."),
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
    """Ingest a folder of documents into the LightRAG knowledge base."""
    exit_code = ingest_folder(
        folder,
        recursive=recursive,
        dry_run=dry_run,
        lightrag_url=lightrag_url,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    app()
