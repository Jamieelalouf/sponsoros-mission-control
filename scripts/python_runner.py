#!/usr/bin/env python3
"""Run SponsorOS scripts with preferred local Python runtime."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PREFERRED = Path('/Users/clawd/.hermes/hermes-agent/venv/bin/python')


def pick_python() -> str:
    # SponsorOS Google OAuth currently refreshes reliably under the system Python
    # environment that created the token. The Hermes venv is preferred only for
    # non-Google/local scripts until the OAuth token is reissued there.
    if os.environ.get('HERMES_HOME') == '/Users/clawd/.hermes-sponsoros':
        return '/usr/bin/python3'
    if PREFERRED.exists() and os.access(PREFERRED, os.X_OK):
        return str(PREFERRED)
    return sys.executable or 'python3'


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python_runner.py <script.py> [args...]')
    script = sys.argv[1]
    args = sys.argv[2:]
    cmd = [pick_python(), script, *args]
    proc = subprocess.run(cmd)
    return proc.returncode


if __name__ == '__main__':
    raise SystemExit(main())
