#!/usr/bin/env python3
"""Verify live CRM state after optional live writes."""

from __future__ import annotations

import json

from sponsoros_google import build_sheets_service, read_sheet_rows, rows_to_dicts


def main() -> int:
    svc = build_sheets_service(['https://www.googleapis.com/auth/spreadsheets'])
    leads = rows_to_dicts(read_sheet_rows(svc, 'Leads'))
    approvals = rows_to_dicts(read_sheet_rows(svc, 'Approvals'))
    source_counts = {}
    for lead in leads:
        src = lead.get('source', 'unknown')
        source_counts[src] = source_counts.get(src, 0) + 1

    sample_leads = [
        lead for lead in leads
        if (lead.get('source') or '').lower() == 'sample'
        or (lead.get('lead_id') or '').lower().startswith('lead_demo')
        or (lead.get('source_url') or '').lower().startswith('sample://')
    ]
    sample_approvals = [
        approval for approval in approvals
        if (approval.get('approval_id') or '').lower().startswith('appr_demo')
        or (approval.get('lead_id') or '').lower().startswith('lead_demo')
        or 'sample dry-run approval' in (approval.get('notes') or '').lower()
        or 'sample copy only' in (approval.get('draft_body') or '').lower()
    ]
    if sample_leads or sample_approvals:
        raise SystemExit(json.dumps({
            'status': 'failed',
            'sample_leads': len(sample_leads),
            'sample_approvals': len(sample_approvals),
        }, indent=2))

    print(json.dumps({
        'status': 'ok',
        'lead_count': len(leads),
        'approval_count': len(approvals),
        'source_counts': source_counts,
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
