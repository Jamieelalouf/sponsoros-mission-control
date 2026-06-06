#!/usr/bin/env python3
"""Generate dashboard aggregates from live CRM sheet or local sample fallback."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sponsoros_google import SponsorOSEnvironmentError, build_sheets_service, read_sheet_rows, rows_to_dicts

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PATH = ROOT / 'data' / 'sample.json'
OUTPUT_PATH = ROOT / 'data' / 'dashboard.json'
EXPECTED_TABS = ['Leads', 'Approvals', 'Inbox', 'Agent_Logs', 'Settings']


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_sample_dashboard() -> dict[str, Any]:
    sample = json.loads(SAMPLE_PATH.read_text(encoding='utf-8'))
    leads = sample.get('leads', [])
    approvals = sample.get('approvals', [])
    stage_counts = Counter(lead.get('stage', 'unknown') for lead in leads)
    approval_status_counts = Counter(item.get('status', 'unknown') for item in approvals)
    return {
        'pipeline_counts': {
            'total_leads': len(leads),
            'by_stage': dict(stage_counts),
            'approvals_total': len(approvals),
            'approvals_by_status': dict(approval_status_counts),
        },
        'lead_queue': leads,
        'approval_queue': approvals,
        'inbox_status': sample.get('inbox', {}),
        'agent_activity': sample.get('agent_activity', []),
        'blockers': sample.get('blockers', []),
        'next_actions': sample.get('next_actions', []),
        'executive': {
            'high_fit_leads': sum(1 for l in leads if int(l.get('fit_score', 0) or 0) >= 70),
            'pending_approvals': sum(1 for a in approvals if (a.get('status') or '').lower() in {'pending', 'edited'}),
            'inbox_needs_response': sample.get('inbox', {}).get('waiting', 0),
        },
    }


def _live_to_dashboard() -> dict[str, Any]:
    service = build_sheets_service(['https://www.googleapis.com/auth/spreadsheets'])
    tab_data: dict[str, list[dict[str, str]]] = {}
    for tab in EXPECTED_TABS:
        tab_data[tab] = rows_to_dicts(read_sheet_rows(service, tab))

    leads = tab_data['Leads']
    approvals = tab_data['Approvals']
    inbox_rows = tab_data['Inbox']
    agent_logs = tab_data['Agent_Logs']

    stage_counts = Counter((lead.get('status') or 'unknown') for lead in leads)
    approval_status_counts = Counter((item.get('status') or 'unknown') for item in approvals)

    unread = sum(1 for row in inbox_rows if (row.get('status', '').lower() in {'new', 'unread', 'pending'}))
    waiting = sum(1 for row in inbox_rows if ((row.get('status', '').lower() in {'waiting', 'needs_reply'}) or row.get('needs_response') == 'yes'))
    starred = sum(1 for row in inbox_rows if (row.get('priority', '').lower() in {'high', 'starred'}))
    last_sync = max([r.get('received_at', '') for r in inbox_rows if r.get('received_at')] + ['live-sheet'])

    blockers = [
        row.get('notes', '')
        for row in approvals
        if (row.get('status', '').lower() in {'pending', 'edited'}) and row.get('notes')
    ][:8]

    high_fit = sum(1 for l in leads if int((l.get('fit_score') or '0').strip() or 0) >= 70)
    pending_appr = sum(1 for a in approvals if (a.get('status') or '').lower() in {'pending', 'edited'})

    next_actions = [
        'Open approval cockpit (ZERO SEND PATH)',
        'Triage inbox needs_response threads',
        'Run Scout dry-run and review fit/confidence',
    ]

    return {
        'pipeline_counts': {
            'total_leads': len(leads),
            'by_stage': dict(stage_counts),
            'approvals_total': len(approvals),
            'approvals_by_status': dict(approval_status_counts),
        },
        'lead_queue': leads[:100],
        'approval_queue': approvals[:100],
        'inbox_status': {
            'unread': unread,
            'starred': starred,
            'waiting': waiting,
            'last_sync': last_sync,
        },
        'agent_activity': agent_logs[:50],
        'blockers': blockers,
        'next_actions': next_actions,
        'settings': tab_data['Settings'],
        'executive': {
            'high_fit_leads': high_fit,
            'pending_approvals': pending_appr,
            'inbox_needs_response': waiting,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['auto', 'live', 'sample'], default='auto')
    args = parser.parse_args()

    source = args.source
    fallback_reason = None

    if source == 'sample':
        dashboard = load_sample_dashboard()
        resolved_source = 'sample'
    else:
        try:
            dashboard = _live_to_dashboard()
            resolved_source = 'live'
        except Exception as exc:
            if source == 'live':
                raise
            dashboard = load_sample_dashboard()
            resolved_source = 'sample_fallback'
            fallback_reason = str(exc) if isinstance(exc, SponsorOSEnvironmentError) else f'live_sheet_unavailable:{type(exc).__name__}'

    dashboard['source'] = {
        'mode_requested': source,
        'mode_resolved': resolved_source,
        'fallback_reason': fallback_reason,
        'generated_at': utc_now(),
        'sample_fallback_labeled': resolved_source in {'sample', 'sample_fallback'},
        'badge': 'LIVE' if resolved_source == 'live' else 'SAMPLE',
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(dashboard, indent=2), encoding='utf-8')

    print(f'Wrote {OUTPUT_PATH} with source={resolved_source}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
