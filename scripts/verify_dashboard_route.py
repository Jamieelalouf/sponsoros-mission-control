#!/usr/bin/env python3
"""Lightweight check that dashboard browser route assets are present."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    index = ROOT / 'index.html'
    preview = ROOT / 'public' / 'standalone-preview.html'
    cockpit = ROOT / 'public' / 'approval-cockpit.html'

    for p in [index, preview]:
        if not p.exists():
            raise SystemExit(f'Missing dashboard route file: {p}')
        t = p.read_text(encoding='utf-8')
        if '/data/dashboard.json' not in t:
            raise SystemExit(f'Dashboard route missing data binding: {p}')

    if not cockpit.exists():
        raise SystemExit(f'Missing dashboard route file: {cockpit}')
    cockpit_text = cockpit.read_text(encoding='utf-8')
    if '/data/dashboard.json' not in cockpit_text:
        raise SystemExit(f'Approval cockpit missing dashboard data binding: {cockpit}')
    if 'ZERO SEND / REVIEW ONLY' not in cockpit_text:
        raise SystemExit(f'Approval cockpit missing zero-send badge: {cockpit}')
    print('dashboard route assets ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
