#!/usr/bin/env python3
"""
Audit (and optionally fix) projects whose stored `current_js` field is
corrupted by the old `validate_js` regex comment-stripper.

Background:
    Until 2026-04-08, validate_js() in backend/app/routes/generator.py ran a
    naive `/\\*[\\s\\S]*?\\*/` block-comment regex on any js >20KB. That regex
    has no awareness of strings, regex literals, or template literals — when
    LLM-generated JS contained an inline `<style>/* ... */</style>` literal,
    or a string literal that happened to contain `/*` followed later by a
    real comment's `*/`, the regex matched across string boundaries and
    chopped arbitrary content. The result was JS that fails to parse with
    "Unexpected token '.'" or "Unexpected identifier 'document'", killing
    all interactive JS on the deployed site.

    The unsafe stripper was removed in commit 0e3bd15. This script finds
    projects whose `current_js` was already corrupted before that fix, and
    optionally regenerates fresh JS by re-running stage_3_js on the project's
    current HTML.

Usage:
    cd backend
    python -m scripts.audit_corrupted_js                # audit only (read-only)
    python -m scripts.audit_corrupted_js --dry-run      # audit + show what would be fixed
    python -m scripts.audit_corrupted_js --fix          # audit + actually regenerate
    python -m scripts.audit_corrupted_js --fix --limit 5
    python -m scripts.audit_corrupted_js --fix --user-id 42
    python -m scripts.audit_corrupted_js --fix --project-id <uuid>

Modes:
    audit (default):
        Read-only. For every non-deleted project with a non-empty
        current_js, parse-check the JS. Print a summary of how many are
        broken and list their IDs/names. Zero LLM calls, zero DB writes.

    --dry-run:
        Same as audit, plus print the exact UPDATE statements that would
        run. Still zero DB writes.

    --fix:
        For every broken project, call stage_3_js(current_html) to
        regenerate JS, validate it parses, and write the new JS to
        projects.current_js. Each fix costs ~1 LLM call (Claude Sonnet).
        Concurrency is limited to avoid rate-limiting.

JS parse check:
    Uses `node --check` (Node.js syntax-only validation). If node is not
    on PATH, falls back to a coarse heuristic that catches the two known
    failure modes ("Unexpected token '.'" and "Unexpected identifier
    'document'") via line-by-line regex inspection. The heuristic is
    weaker — strongly prefer running this script on a host with node
    installed.

Safety:
    - Soft-deleted projects (deleted_at IS NOT NULL) are skipped.
    - Projects with empty current_js are skipped (nothing to corrupt).
    - Projects whose current_js is already valid are skipped.
    - In --fix mode, if regeneration produces JS that *also* fails to
      parse, the original (broken) JS is left in place and the failure
      is logged. Better a broken row than a doubly-broken row.
    - --fix uses a concurrency semaphore (default 3) to avoid hammering
      the LLM provider. Override with --concurrency.
"""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import NamedTuple

# Make `app.*` importable when running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session  # type: ignore


# ─── JS parse-check ────────────────────────────────────────────────────────


_NODE_AVAILABLE = shutil.which("node") is not None


class ParseResult(NamedTuple):
    ok: bool
    error: str  # empty string if ok


def js_parse_check(js: str) -> ParseResult:
    """Return (ok, error_message) for a JS string.

    Prefers `node --check` (real V8 parser). Falls back to a coarse
    heuristic if node isn't installed.
    """
    if not js or not js.strip():
        return ParseResult(True, "")

    if _NODE_AVAILABLE:
        # node --check expects a file. Use a temp file so we don't have
        # to pipe through stdin (some node versions are picky about that).
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(js)
            tmp_path = f.name
        try:
            proc = subprocess.run(
                ["node", "--check", tmp_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                return ParseResult(True, "")
            # node --check stderr looks like:
            #   /tmp/xxx.js:LINE
            #   <offending line>
            #   <caret>
            #   <empty>
            #   <ErrorType>: <message>
            # We want the file:LINE marker AND the final error type.
            err_lines = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
            line_marker = ""
            error_type = ""
            for l in err_lines:
                # File:line marker → strip the directory portion for brevity
                if l.endswith(".js") is False and ":" in l and "/" in l:
                    # e.g. "/tmp/xxx.js:177"
                    line_marker = "line " + l.rsplit(":", 1)[-1]
                # Real error line: "SyntaxError: Unexpected token..."
                if "Error:" in l or "error:" in l:
                    error_type = l
                    break
            msg = " — ".join(filter(None, [line_marker, error_type])) or err_lines[-1]
            return ParseResult(False, msg[:200])
        except subprocess.TimeoutExpired:
            return ParseResult(False, "node --check timed out")
        except Exception as e:
            return ParseResult(False, f"node --check exception: {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # Fallback heuristic: catch the two known failure signatures.
    # This is weaker than node --check — it misses lots of real errors.
    # Print a warning so the operator knows to install node for real audits.
    return _heuristic_parse_check(js)


def _heuristic_parse_check(js: str) -> ParseResult:
    """Coarse fallback when node isn't installed.

    Looks for specific damage patterns left by the old regex stripper:
      1. A line whose first non-whitespace char is `.` (orphan chained
         call after a chopped previous statement).
      2. Two top-level statements glued together with no separator
         (e.g. `something()document.foo`) — heuristic on `(\\)\\s*[a-zA-Z_$]).
      3. Severely unbalanced braces / parens / brackets across the file.
    """
    lines = js.split("\n")
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith(".") and not stripped.startswith(".."):
            # `.` at line start is almost always a chopped chained call.
            # Genuine `.` continuations are valid only if the previous
            # line ends in an operator/comma — too noisy to check fully,
            # so just flag it.
            return ParseResult(False, f"line {i}: orphan '.' at start of line")

    # Glued statements: `)` immediately followed by an identifier.
    import re

    glued = re.search(r"\)\s*[A-Za-z_$][A-Za-z0-9_$]*\s*[\.\(]", js)
    if glued:
        snippet = js[max(0, glued.start() - 10) : glued.end() + 10]
        return ParseResult(False, f"glued statements near: {snippet!r}")

    # Brace balance — strip strings/regexes first (best-effort)
    stripped_js = re.sub(r'"(?:[^"\\]|\\.)*"', '""', js)
    stripped_js = re.sub(r"'(?:[^'\\]|\\.)*'", "''", stripped_js)
    stripped_js = re.sub(r"`(?:[^`\\]|\\.)*`", "``", stripped_js)
    stripped_js = re.sub(r"//[^\n]*", "", stripped_js)
    stripped_js = re.sub(r"/\*[\s\S]*?\*/", "", stripped_js)
    if stripped_js.count("{") != stripped_js.count("}"):
        return ParseResult(False, "unbalanced { } braces")
    if stripped_js.count("(") != stripped_js.count(")"):
        return ParseResult(False, "unbalanced ( ) parens")

    return ParseResult(True, "")


# ─── DB scan ───────────────────────────────────────────────────────────────


class BrokenProject(NamedTuple):
    id: str
    user_id: int
    name: str
    js_len: int
    error: str


async def _has_column(session: AsyncSession, table: str, column: str) -> bool:
    """Check if a column exists in a table (handles model/migration drift)."""
    q = text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c LIMIT 1"
    )
    res = await session.execute(q, {"t": table, "c": column})
    return res.scalar_one_or_none() is not None


async def scan_for_broken(
    session: AsyncSession,
    user_id: int | None,
    project_id: str | None,
    limit: int | None,
) -> tuple[list[BrokenProject], int]:
    """Scan projects table. Return (broken_list, total_scanned).

    Uses a raw SQL SELECT (not the SQLAlchemy model) to tolerate
    model/migration drift — the model defines `deleted_at` but some local
    DBs don't have it yet.
    """
    has_deleted_at = await _has_column(session, "projects", "deleted_at")

    where_clauses: list[str] = []
    params: dict[str, object] = {}
    if has_deleted_at:
        where_clauses.append("deleted_at IS NULL")
    if user_id is not None:
        where_clauses.append("user_id = :user_id")
        params["user_id"] = user_id
    if project_id is not None:
        where_clauses.append("id = :project_id")
        params["project_id"] = project_id
    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    sql = text(
        f"SELECT id, user_id, name, current_js FROM projects{where_sql} ORDER BY updated_at DESC"
    )
    result = await session.execute(sql, params)
    rows = result.fetchall()

    broken: list[BrokenProject] = []
    scanned = 0
    for row in rows:
        scanned += 1
        js = row.current_js or ""
        if not js.strip():
            continue
        check = js_parse_check(js)
        if not check.ok:
            broken.append(
                BrokenProject(
                    id=row.id,
                    user_id=row.user_id,
                    name=row.name or "(untitled)",
                    js_len=len(js),
                    error=check.error,
                )
            )
        if limit is not None and len(broken) >= limit:
            break

    return broken, scanned


# ─── Fix path ──────────────────────────────────────────────────────────────


async def regenerate_one(
    session: AsyncSession,
    project_id: str,
    sem: asyncio.Semaphore,
) -> tuple[bool, str]:
    """Regenerate JS for one project. Returns (ok, message)."""
    # Lazy-import to avoid loading the heavy LLM stack during audit-only runs
    from app.routes.generator import stage_3_js  # type: ignore

    async with sem:
        # Raw SQL — see note in scan_for_broken about model/migration drift.
        row = (
            await session.execute(
                text("SELECT current_html FROM projects WHERE id = :id"),
                {"id": project_id},
            )
        ).first()
        if row is None:
            return False, "project not found"
        html = row.current_html or ""
        if not html.strip():
            return False, "project has empty html — nothing to regenerate against"

        try:
            new_js = await stage_3_js(html, session_id=f"backfill-{project_id[:8]}")
        except Exception as e:
            return False, f"stage_3_js failed: {e}"

        # Sanity check: the new JS must parse, otherwise leave the row alone.
        check = js_parse_check(new_js)
        if not check.ok:
            return False, f"regenerated JS still does not parse: {check.error}"

        await session.execute(
            text("UPDATE projects SET current_js = :js, updated_at = NOW() WHERE id = :id"),
            {"js": new_js, "id": project_id},
        )
        await session.commit()
        return True, f"regenerated {len(new_js):,} chars"


# ─── Main ──────────────────────────────────────────────────────────────────


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit (and optionally fix) projects with corrupted JS",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Audit + print what would be fixed (no DB writes, no LLM calls)",
    )
    mode.add_argument(
        "--fix",
        action="store_true",
        help="Audit + regenerate JS for every broken project (DB writes + LLM calls)",
    )
    parser.add_argument("--user-id", type=int, default=None, help="Restrict to one user")
    parser.add_argument("--project-id", type=str, default=None, help="Restrict to one project")
    parser.add_argument("--limit", type=int, default=None, help="Stop after finding N broken projects")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Max concurrent regenerate calls in --fix mode (default: 3)",
    )
    args = parser.parse_args()

    if not _NODE_AVAILABLE:
        print(
            "⚠️  WARNING: `node` not found on PATH. Falling back to heuristic\n"
            "   parse-checking, which is much weaker than `node --check`. Install\n"
            "   Node.js for accurate audits: https://nodejs.org/\n",
            file=sys.stderr,
        )

    print(f"🔍 Scanning projects table (filters: user_id={args.user_id} project_id={args.project_id} limit={args.limit})...")
    t0 = time.time()

    async with async_session() as session:
        broken, scanned = await scan_for_broken(
            session,
            user_id=args.user_id,
            project_id=args.project_id,
            limit=args.limit,
        )

    elapsed = time.time() - t0
    print(f"✅ Scan complete in {elapsed:.1f}s — checked {scanned} projects, found {len(broken)} broken\n")

    if not broken:
        print("🎉 No corrupted JS found. Nothing to do.")
        return 0

    # Print the broken list
    print(f"{'PROJECT ID':<38} {'USER':<6} {'JS LEN':<10} {'NAME':<30} ERROR")
    print("─" * 120)
    for b in broken:
        name = (b.name[:27] + "...") if len(b.name) > 30 else b.name
        print(f"{b.id:<38} {b.user_id:<6} {b.js_len:<10,} {name:<30} {b.error}")
    print()

    if not (args.dry_run or args.fix):
        print(f"📊 Audit complete. {len(broken)} project(s) need regeneration.")
        print("   Re-run with --dry-run to preview, or --fix to regenerate.")
        return 0

    if args.dry_run:
        print(f"🧪 DRY RUN: would call stage_3_js() for {len(broken)} project(s).")
        print(f"   Estimated cost: ~{len(broken)} Claude Sonnet API calls.")
        print(f"   Re-run with --fix to actually regenerate.")
        return 0

    # --fix path
    print(f"🛠️  FIX MODE: regenerating JS for {len(broken)} project(s) (concurrency={args.concurrency})...")
    print()

    sem = asyncio.Semaphore(args.concurrency)
    fixed = 0
    failed = 0
    failures: list[tuple[str, str]] = []

    async def _fix_one(b: BrokenProject) -> None:
        nonlocal fixed, failed
        async with async_session() as session:
            ok, msg = await regenerate_one(session, b.id, sem)
        if ok:
            fixed += 1
            print(f"  ✅ {b.id} ({b.name[:30]}) — {msg}")
        else:
            failed += 1
            failures.append((b.id, msg))
            print(f"  ❌ {b.id} ({b.name[:30]}) — {msg}")

    await asyncio.gather(*(_fix_one(b) for b in broken))

    print()
    print(f"📊 Fix complete: {fixed} regenerated, {failed} failed (out of {len(broken)} broken)")
    if failures:
        print()
        print("Failures (these projects still have corrupted JS):")
        for pid, msg in failures:
            print(f"  - {pid}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
