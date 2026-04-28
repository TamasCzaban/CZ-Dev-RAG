"""Sync personal knowledge sources into data/input/ for ingestion.

Reads a hardcoded manifest of canonical paths (Claude Code memory files,
LEARNINGS files, project docs) and copies them into ``data/input/`` under a
human-navigable folder layout. Files with YAML frontmatter (memory files) are
preprocessed so the description and type become first-class searchable content.

The script is idempotent: unchanged files are skipped. Missing sources surface
as warnings but do not fail the run — sources move around as projects evolve.

Run from the repo root:

    uv run python scripts/sync_personal_kb.py
    uv run python scripts/sync_personal_kb.py --dry-run
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(add_completion=False, help=__doc__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_INPUT = REPO_ROOT / "data" / "input"

HOME = Path(os.path.expanduser("~"))
CLAUDE_DIR = HOME / ".claude"
PROJECTS = HOME / "projects"


@dataclass(frozen=True)
class Entry:
    src: Path
    dest: Path
    is_memory: bool = False


def _e(src: Path, *dest_parts: str, is_memory: bool = False) -> Entry:
    return Entry(src=src, dest=DATA_INPUT.joinpath(*dest_parts), is_memory=is_memory)


def _personal() -> list[Entry]:
    base = CLAUDE_DIR / "projects" / "C--Users-Toma" / "memory"
    return [
        _e(base / "me.md", "personal", "me.md", is_memory=True),
        _e(base / "user_profile.md", "personal", "user_profile.md", is_memory=True),
        _e(base / "zsombor.md", "personal", "zsombor.md", is_memory=True),
        _e(base / "project_portfolio.md", "personal", "project_portfolio.md", is_memory=True),
        _e(base / "MEMORY.md", "personal", "MEMORY_index.md"),
        _e(CLAUDE_DIR / "CLAUDE.md", "personal", "claude_global.md"),
    ]


def _project_memories() -> list[Entry]:
    project_dirs = {
        "C--Users-Toma-projects": "workspace",
        "C--Users-Toma-projects-bemer-crm": "bemer_crm",
        "C--Users-Toma-projects-career-ops": "career_ops",
        "C--Users-Toma-projects-portfolio-sites-czdev-site-new": "portfolio_sites_czdev",
        "C--Users-Toma-PycharmProjects-Bemer": "bemer_pycharm",
    }
    entries: list[Entry] = []
    for src_slug, dest_slug in project_dirs.items():
        mem_dir = CLAUDE_DIR / "projects" / src_slug / "memory"
        if not mem_dir.is_dir():
            continue
        for src_file in sorted(mem_dir.glob("*.md")):
            entries.append(
                _e(
                    src_file,
                    "memory",
                    dest_slug,
                    src_file.name,
                    is_memory=src_file.name != "MEMORY.md",
                )
            )
    return entries


def _learnings() -> list[Entry]:
    return [
        _e(PROJECTS / "cz_dev_rag" / "LEARNINGS.md", "learnings", "cz_dev_rag.md"),
        _e(PROJECTS / "career_ops" / "data" / "learnings.md", "learnings", "career_ops_data.md"),
    ]


def _project_docs() -> list[Entry]:
    cz = PROJECTS / "cz_dev_rag"
    co = PROJECTS / "career_ops"
    bc = PROJECTS / "bemer_crm"
    ps = PROJECTS / "portfolio_sites"
    return [
        _e(cz / "CLAUDE.md", "projects", "cz_dev_rag", "CLAUDE.md"),
        _e(cz / "ROADMAP.md", "projects", "cz_dev_rag", "ROADMAP.md"),
        _e(cz / "STATE.md", "projects", "cz_dev_rag", "STATE.md"),
        _e(cz / "docs" / "ARCHITECTURE.md", "projects", "cz_dev_rag", "docs", "ARCHITECTURE.md"),
        _e(cz / "docs" / "DECISIONS.md", "projects", "cz_dev_rag", "docs", "DECISIONS.md"),
        _e(cz / "docs" / "RUNBOOK.md", "projects", "cz_dev_rag", "docs", "RUNBOOK.md"),
        _e(cz / "docs" / "SECURITY.md", "projects", "cz_dev_rag", "docs", "SECURITY.md"),
        _e(cz / "docs" / "OBSERVABILITY.md", "projects", "cz_dev_rag", "docs", "OBSERVABILITY.md"),
        _e(co / "CLAUDE.md", "projects", "career_ops", "CLAUDE.md"),
        _e(co / "docs" / "ARCHITECTURE.md", "projects", "career_ops", "docs", "ARCHITECTURE.md"),
        _e(co / "docs" / "SETUP.md", "projects", "career_ops", "docs", "SETUP.md"),
        _e(co / "docs" / "CODEX.md", "projects", "career_ops", "docs", "CODEX.md"),
        _e(co / "docs" / "CUSTOMIZATION.md", "projects", "career_ops", "docs", "CUSTOMIZATION.md"),
        _e(bc / "CLAUDE.md", "projects", "bemer_crm", "CLAUDE.md"),
        _e(ps / "CLAUDE.md", "projects", "portfolio_sites", "CLAUDE.md"),
    ]


def manifest() -> list[Entry]:
    return _personal() + _project_memories() + _learnings() + _project_docs()


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)


def preprocess_memory(text: str) -> str:
    """Convert YAML frontmatter into a markdown header + blockquote.

    Memory files have ``name``, ``description``, ``type`` keys. Promoting these
    to markdown means the entity-extraction LLM treats them as first-class
    content rather than as a token cloud.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return text
    fm_block, body = match.group(1), match.group(2).lstrip()
    fm: dict[str, str] = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    name = fm.get("name", "Memory")
    description = fm.get("description", "").strip()
    mem_type = fm.get("type", "").strip()
    header = f"# {name}\n"
    if description:
        suffix = f" (memory type: {mem_type})" if mem_type else ""
        header += f"\n> {description}{suffix}\n"
    return f"{header}\n{body}"


def _read(src: Path, *, is_memory: bool) -> str:
    text = src.read_text(encoding="utf-8", errors="replace")
    return preprocess_memory(text) if is_memory else text


@app.command()
def main(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--no-dry-run", help="Print actions without writing."),
    ] = False,
) -> None:
    entries = manifest()
    copied = 0
    skipped = 0
    missing: list[Path] = []
    written: list[Path] = []

    for e in entries:
        if not e.src.is_file():
            missing.append(e.src)
            continue
        new_content = _read(e.src, is_memory=e.is_memory)
        if e.dest.is_file():
            old_content = e.dest.read_text(encoding="utf-8", errors="replace")
            if old_content == new_content:
                skipped += 1
                continue
        if dry_run:
            written.append(e.dest)
            copied += 1
            continue
        e.dest.parent.mkdir(parents=True, exist_ok=True)
        e.dest.write_text(new_content, encoding="utf-8")
        written.append(e.dest)
        copied += 1

    typer.echo(f"Manifest: {len(entries)} entries")
    typer.echo(f"  copied/updated: {copied}{' (dry-run)' if dry_run else ''}")
    typer.echo(f"  skipped (unchanged): {skipped}")
    typer.echo(f"  missing source: {len(missing)}")
    for m in missing:
        typer.echo(f"    WARNING: missing {m}", err=True)

    if copied and not dry_run:
        rel = DATA_INPUT.relative_to(REPO_ROOT)
        typer.echo("\nNext step:")
        typer.echo(f"  uv run python scripts/ingest.py {rel}/ --recursive")

    sys.exit(0)


if __name__ == "__main__":
    app()
