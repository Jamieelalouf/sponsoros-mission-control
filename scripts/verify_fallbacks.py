#!/usr/bin/env python3
"""Verify live/safe fallback behavior for dashboard generation."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "data" / "dashboard.json"
SCRIPT = ROOT / "scripts" / "generate_dashboard_data.py"


def _run(cmd: list[str], env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=True, capture_output=True, text=True)


def main() -> int:
    env = os.environ.copy()
    env.pop("HERMES_HOME", None)
    original_dashboard = DASHBOARD.read_text(encoding="utf-8") if DASHBOARD.exists() else None

    try:
        _run(["python3", str(SCRIPT), "--source", "auto"], env)
        payload = json.loads(DASHBOARD.read_text(encoding="utf-8"))
        source = payload.get("source", {})

        if source.get("mode_requested") != "auto":
            raise SystemExit("Expected mode_requested=auto")
        if source.get("mode_resolved") not in {"sample_fallback", "sample", "live"}:
            raise SystemExit("Unexpected mode_resolved")
        if source.get("mode_resolved") != "live" and not source.get("sample_fallback_labeled"):
            raise SystemExit("Sample fallback should be explicitly labeled")
    finally:
        if original_dashboard is not None:
            DASHBOARD.write_text(original_dashboard, encoding="utf-8")
        elif DASHBOARD.exists():
            DASHBOARD.unlink()

    print("fallback behavior ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
