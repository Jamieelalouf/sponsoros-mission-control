#!/usr/bin/env python3
"""Verify approval cockpit exists and preserves strict no-send UI guardrails."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COCKPIT = ROOT / 'public' / 'approval-cockpit.html'

REQUIRED = [
    'ZERO SEND / REVIEW ONLY',
    'Save Local Browser State',
    'Export Local JSON',
    'Import Local JSON',
    'Approve',
    'Reject',
    'Mark Edited',
    '/data/dashboard.json',
]

BANNED = [
    'mailto:',
    'messages()' + '.send(',
    'drafts()' + '.create(',
    'drafts()' + '.send(',
    'messages()' + '.modify(',
    'gmail' + '.modify',
    'smtp',
    'fetch("https://',
    "fetch('https://",
]


def main() -> int:
    if not COCKPIT.exists():
        raise SystemExit(f'Missing approval cockpit UI: {COCKPIT}')

    text = COCKPIT.read_text(encoding='utf-8')

    for marker in REQUIRED:
        if marker not in text:
            raise SystemExit(f'Approval cockpit missing required marker: {marker}')

    lower_text = text.lower()
    for marker in BANNED:
        if marker.lower() in lower_text:
            raise SystemExit(f'Approval cockpit contains banned send marker: {marker}')

    print('approval cockpit ui guardrails ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
