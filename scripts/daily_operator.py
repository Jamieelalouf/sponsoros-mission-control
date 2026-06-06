#!/usr/bin/env python3
"""Daily Operator scaffold.

Runs local daily refresh sequence without send paths or cron creation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / 'data' / 'reports'
OBSIDIAN_PATH = Path.home() / 'Obsidian' / 'Domains' / 'SponsorOS'


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], env: dict[str, str]) -> dict[str, str]:
    p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    return {
        'cmd': ' '.join(cmd),
        'code': str(p.returncode),
        'stdout': (p.stdout or '').strip()[-1200:],
        'stderr': (p.stderr or '').strip()[-1200:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-live-scout', action='store_true', help='Explicitly allow live Scout write step')
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault('HERMES_HOME', '/Users/clawd/.hermes-sponsoros')

    steps = []
    steps.append(run(['python3', 'scripts/scout_pipeline.py', 'dry-run', '--limit', '50'], env))
    if args.write_live_scout:
        steps.append(run(['python3', 'scripts/scout_pipeline.py', 'write-live', '--limit', '50'], env))
    steps.append(run(['python3', 'scripts/sync_gmail_inbox.py', '--limit', '25'], env))
    steps.append(run(['python3', 'scripts/generate_dashboard_data.py', '--source', 'auto'], env))

    report = {
        'generated_at': now(),
        'scout_live_write_requested': args.write_live_scout,
        'steps': steps,
        'no_send_path': True,
        'no_cron_created': True,
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    file_name = f"daily_operator_{datetime.now().strftime('%Y%m%d')}.json"
    out = REPORTS / file_name
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')

    if OBSIDIAN_PATH.exists():
        OBSIDIAN_PATH.mkdir(parents=True, exist_ok=True)
        md = OBSIDIAN_PATH / f"SponsorOS_Daily_{datetime.now().strftime('%Y-%m-%d')}.md"
        lines = [
            '# SponsorOS Daily Operator Report',
            f'- Generated: {report["generated_at"]}',
            f'- Scout live write requested: {args.write_live_scout}',
            '- Guardrails: no-send=true; no-cron=true',
            '',
            '## Steps',
        ]
        for s in steps:
            lines.append(f"- `{s['cmd']}` -> code {s['code']}")
            if s['stdout']:
                lines.append(f"  - stdout: {s['stdout'][:180]}")
            if s['stderr']:
                lines.append(f"  - stderr: {s['stderr'][:180]}")
        md.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print(f'Wrote {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
