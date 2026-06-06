#!/usr/bin/env python3
"""Validate expected dashboard.json schema (lightweight structural check)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "data" / "dashboard.json"

REQUIRED_TOP_LEVEL = {
    "pipeline_counts",
    "lead_queue",
    "approval_queue",
    "inbox_status",
    "agent_activity",
    "blockers",
    "next_actions",
    "source",
}

REQUIRED_SOURCE = {
    "mode_requested",
    "mode_resolved",
    "fallback_reason",
    "generated_at",
    "sample_fallback_labeled",
}


def main() -> int:
    payload = json.loads(DASHBOARD.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_TOP_LEVEL - set(payload.keys()))
    if missing:
        raise SystemExit(f"Missing dashboard keys: {missing}")

    source = payload["source"]
    missing_source = sorted(REQUIRED_SOURCE - set(source.keys()))
    if missing_source:
        raise SystemExit(f"Missing source keys: {missing_source}")

    counts = payload["pipeline_counts"]
    for k in ["total_leads", "approvals_total"]:
        if k not in counts:
            raise SystemExit(f"Missing pipeline count: {k}")

    print("dashboard schema ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
