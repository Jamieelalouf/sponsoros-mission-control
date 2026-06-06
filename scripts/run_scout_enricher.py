#!/usr/bin/env python3
"""Backward-compatible wrapper for Scout pipeline dry-run."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--append-approvals', action='store_true', help='Deprecated in Block 2; use draft generation script')
    parser.add_argument('--limit', type=int, default=50)
    args = parser.parse_args()

    if args.append_approvals:
        print('append-approvals is deprecated; run draft generation script after approval stage.')

    cmd = [sys.executable, str(ROOT / 'scripts' / 'scout_pipeline.py'), 'dry-run', '--limit', str(args.limit)]
    return subprocess.run(cmd, cwd=str(ROOT), check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
