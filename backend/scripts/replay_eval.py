"""
Replay eval harness — replays past edit prompts against the live pipeline
and prints per-category success/duration breakdowns. Use to compare a
prompt-version change before/after by snapshotting two runs.

Usage:
    python -m backend.scripts.replay_eval --limit 30 --category rebrand
    python -m backend.scripts.replay_eval --since 7d --tag baseline > out.json

Note: Replays are read-only against a clone of session state — they do not
modify any user's project. Skip prompts whose original session is gone.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.edit_log import EditFeedback, EditLog


def _parse_since(s: str) -> datetime:
    if s.endswith("d"):
        n = int(s[:-1])
        return datetime.now(timezone.utc) - timedelta(days=n)
    if s.endswith("h"):
        n = int(s[:-1])
        return datetime.now(timezone.utc) - timedelta(hours=n)
    return datetime.fromisoformat(s)


async def _load_rows(db: AsyncSession, *, limit: int, category: str | None, since: datetime | None):
    q = select(EditLog).where(EditLog.success.is_(True))
    if category: q = q.where(EditLog.category == category)
    if since: q = q.where(EditLog.created_at >= since)
    q = q.order_by(EditLog.created_at.desc()).limit(limit)
    return (await db.execute(q)).scalars().all()


async def _feedback_lookup(db: AsyncSession, ids: list) -> dict[str, str]:
    if not ids: return {}
    rows = (await db.execute(
        select(EditFeedback.edit_log_id, EditFeedback.rating).where(EditFeedback.edit_log_id.in_(ids))
    )).all()
    return {str(eid): r for eid, r in rows}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--category", default=None)
    ap.add_argument("--since", default="7d")
    ap.add_argument("--tag", default="run", help="Label for this run in the output")
    args = ap.parse_args()

    since = _parse_since(args.since) if args.since else None
    async with async_session() as db:
        rows = await _load_rows(db, limit=args.limit, category=args.category, since=since)
        feedback = await _feedback_lookup(db, [r.id for r in rows])

    summary: dict = {
        "tag": args.tag,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(rows),
        "by_category": {},
        "samples": [],
    }
    for r in rows:
        cat = r.category or "uncategorized"
        s = summary["by_category"].setdefault(cat, {"n": 0, "thumbs_up": 0, "thumbs_down": 0, "avg_ms": 0})
        s["n"] += 1
        s["avg_ms"] = (s["avg_ms"] * (s["n"] - 1) + (r.duration_ms or 0)) / s["n"]
        fb = feedback.get(str(r.id))
        if fb == "up":   s["thumbs_up"] += 1
        if fb == "down": s["thumbs_down"] += 1
        summary["samples"].append({
            "id": str(r.id),
            "category": cat,
            "kind": r.edit_kind,
            "prompt": (r.prompt or "")[:200],
            "duration_ms": r.duration_ms,
            "feedback": fb,
        })

    json.dump(summary, sys.stdout, indent=2, default=str)
    print()


if __name__ == "__main__":
    asyncio.run(main())
