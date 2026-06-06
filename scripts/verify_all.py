#!/usr/bin/env python3
"""Run local verification without permanently changing dashboard source state."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / 'data' / 'dashboard.json'


def run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=True)


def main() -> int:
    original_dashboard = DASHBOARD.read_text(encoding='utf-8') if DASHBOARD.exists() else None
    env = os.environ.copy()
    env.setdefault('PYTHONPYCACHEPREFIX', '/private/tmp/sponsoros-pycache')

    try:
        run(['python3', '-m', 'py_compile', *[str(p) for p in sorted((ROOT / 'scripts').glob('*.py'))]], env)
        run(['python3', 'scripts/scout_pipeline.py', 'dry-run', '--limit', '50'], env)
        run(['python3', 'scripts/verify_scout_output.py'], env)
        run(['python3', 'scripts/generate_dashboard_data.py', '--source', 'auto'], env)
        run(['python3', 'scripts/verify_dashboard_schema.py'], env)
        run(['python3', 'scripts/verify_dashboard_route.py'], env)
        run(['python3', 'scripts/verify_approval_ui.py'], env)
        run(['python3', 'scripts/verify_no_send_paths.py'], env)
        run(['python3', 'scripts/verify_fallbacks.py'], env)

        json.loads((ROOT / 'data' / 'sample.json').read_text(encoding='utf-8'))
        json.loads(DASHBOARD.read_text(encoding='utf-8'))
    finally:
        if original_dashboard is not None:
            DASHBOARD.write_text(original_dashboard, encoding='utf-8')
        elif DASHBOARD.exists():
            DASHBOARD.unlink()

    print('verify all ok; dashboard source state preserved')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
