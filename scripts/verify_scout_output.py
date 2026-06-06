#!/usr/bin/env python3
"""Verify dry-run scout output exists and is structurally valid."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'dry_run_scout_enricher.json'


def main() -> int:
    if not OUT.exists():
        raise SystemExit(f'Missing dry-run output: {OUT}')
    payload = json.loads(OUT.read_text(encoding='utf-8'))
    leads = payload.get('leads', [])
    shortage = payload.get('shortage_reason')
    if not leads and not shortage:
        raise SystemExit('Dry-run scout output has no leads and no structured shortage_reason')

    required = ['company_name', 'source_url', 'location', 'category', 'status', 'fit_score', 'confidence', 'notes', 'discovered_at']
    for i, lead in enumerate(leads[:10], start=1):
        missing = [k for k in required if k not in lead]
        if missing:
            raise SystemExit(f'Lead {i} missing fields: {missing}')
    print(f'scout output ok: leads={len(leads)} shortage_reason={bool(shortage)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
