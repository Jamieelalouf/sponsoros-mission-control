#!/usr/bin/env python3
"""Generate locked outreach draft text into Approvals only.

Rules:
- No Gmail use.
- Writes only to Approvals sheet.
- Generated rows must have sent_at blank and status Pending or Edited.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sponsoros_google import CRM_SHEET_ID, build_sheets_service, read_sheet_rows, rows_to_dicts

SHEETS_RW_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'
ALLOWED_APPROVAL_STATUS = {'Pending', 'Edited'}
ROOT = Path(__file__).resolve().parent.parent
DRY_RUN_REPORT = ROOT / 'data' / 'approval_drafts_dry_run_report.json'
DASHBOARD_JSON = ROOT / 'data' / 'dashboard.json'


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_draft(company: str, category: str, location: str) -> tuple[str, str]:
    subject = f'Sponsor idea for {company}'
    body = (
        f'Hi {company} team,\\n\\n'
        f'We found a potential sponsor-fit angle around {category} activations in {location}. '
        'If useful, we can share a concise concept outline tailored for youth/event audiences.\\n\\n'
        'DRAFT ONLY. ZERO SEND PATH.\\n'
    )
    return subject, body


def _v(row: list[str], index: int | None) -> str:
    if index is None:
        return ''
    return row[index] if index < len(row) else ''


def _write_report(payload: dict) -> None:
    DRY_RUN_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DRY_RUN_REPORT.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')


def _field(row: list[str], column_idx: dict[str, int], key: str) -> str:
    i = column_idx.get(key)
    if i is None:
        return ''
    return row[i] if i < len(row) else ''


def _local_snapshot_rows() -> tuple[list[dict[str, str]], list[list[str]], str]:
    data = json.loads(DASHBOARD_JSON.read_text(encoding='utf-8'))
    leads = data.get('lead_queue', [])
    approval_queue = data.get('approval_queue', [])
    headers = [
        'approval_id', 'lead_id', 'company_name', 'website', 'source_url', 'fit_score',
        'subject_or_hook', 'draft_body', 'status', 'sent_at', 'notes', 'created_at', 'updated_at',
    ]
    rows = [headers]
    for item in approval_queue:
        rows.append([str(item.get(h, '')) for h in headers])
    return leads, rows, 'local_dashboard_snapshot'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=25)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    source_mode = 'live_crm'
    sheets = None
    try:
        sheets = build_sheets_service([SHEETS_RW_SCOPE])
        leads = rows_to_dicts(read_sheet_rows(sheets, 'Leads'))
        approvals_rows = read_sheet_rows(sheets, 'Approvals')
        if not approvals_rows:
            raise SystemExit('Approvals tab missing headers')
    except Exception:
        if not args.dry_run:
            raise
        leads, approvals_rows, source_mode = _local_snapshot_rows()

    headers = approvals_rows[0]
    idx = {h: i for i, h in enumerate(headers)}
    required = ['approval_id', 'lead_id', 'company_name', 'subject_or_hook', 'draft_body', 'status', 'sent_at', 'notes', 'created_at']
    missing = [h for h in required if h not in idx]
    if missing:
        raise SystemExit(f'Approvals headers missing: {missing}')

    lead_id_idx = idx.get('lead_id')
    approval_id_idx = idx.get('approval_id')
    subject_idx = idx.get('subject_or_hook')
    draft_body_idx = idx.get('draft_body')
    status_idx = idx.get('status')
    sent_at_idx = idx.get('sent_at')

    existing_lead_ids: set[str] = set()
    existing_approval_ids: set[str] = set()
    for r in approvals_rows[1:]:
        lead_id = _v(r, lead_id_idx).strip()
        approval_id = _v(r, approval_id_idx).strip()
        if lead_id:
            existing_lead_ids.add(lead_id)
        if approval_id:
            existing_approval_ids.add(approval_id)

    candidates = []
    skipped_existing = 0
    skipped_status = 0
    for lead in leads:
        status = (lead.get('status') or '').strip()
        if status not in {'Proposed', 'Qualified'}:
            skipped_status += 1
            continue
        lead_id = (lead.get('lead_id') or '').strip()
        approval_id = f"apr-{lead_id.replace('lead-', '')}" if lead_id else ''
        if lead_id in existing_lead_ids or (approval_id and approval_id in existing_approval_ids):
            skipped_existing += 1
            continue
        candidates.append(lead)
        if len(candidates) >= args.limit:
            break

    new_rows = []
    prepared_ids: set[str] = set()
    for lead in candidates:
        lead_id = (lead.get('lead_id') or '').strip()
        approval_id = f"apr-{lead_id.replace('lead-', '')}" if lead_id else ''
        if lead_id in prepared_ids:
            continue
        subject, draft = build_draft(lead.get('company_name', 'Partner'), lead.get('industry', 'sponsor'), lead.get('location', 'your market'))
        row = [''] * len(headers)
        row[idx['approval_id']] = approval_id
        row[idx['lead_id']] = lead_id
        row[idx['company_name']] = lead.get('company_name', '')
        if 'contact_email' in idx:
            row[idx['contact_email']] = ''
        if 'channel' in idx:
            row[idx['channel']] = 'email'
        row[idx['subject_or_hook']] = subject
        row[idx['draft_body']] = draft
        row[idx['status']] = 'Pending'
        if 'approved_by' in idx:
            row[idx['approved_by']] = ''
        if 'approved_at' in idx:
            row[idx['approved_at']] = ''
        row[idx['sent_at']] = ''
        source_url = (lead.get('source_url') or '').strip()
        website = (lead.get('website') or '').strip()
        fit_score = (lead.get('fit_score') or '').strip()
        if 'source_url' in idx:
            row[idx['source_url']] = source_url
        if 'website' in idx:
            row[idx['website']] = website
        if 'fit_score' in idx:
            row[idx['fit_score']] = fit_score
        row[idx['notes']] = (
            f"Auto-generated draft only; ZERO SEND PATH; source_url={source_url or 'n/a'}; "
            f"website={website or 'n/a'}; fit_score={fit_score or 'n/a'}"
        )
        row[idx['created_at']] = now()
        if 'updated_at' in idx:
            row[idx['updated_at']] = row[idx['created_at']]
        new_rows.append(row)
        prepared_ids.add(lead_id)

    # verification gate
    for row in new_rows:
        status = row[status_idx]
        sent_at = row[sent_at_idx]
        if status not in ALLOWED_APPROVAL_STATUS or sent_at:
            raise SystemExit('Draft verification failed: status/sent_at policy violation')
        if not row[subject_idx] or not row[draft_body_idx]:
            raise SystemExit('Draft verification failed: missing subject/draft body')
        if row[approval_id_idx] in existing_approval_ids:
            raise SystemExit('Draft verification failed: duplicate approval_id')
        if row[lead_id_idx] in existing_lead_ids:
            raise SystemExit('Draft verification failed: duplicate lead_id')

    report = {
        'mode': 'dry_run' if args.dry_run else 'live',
        'generated_at': now(),
        'lead_total_seen': len(leads),
        'limit': args.limit,
        'candidates_considered': len(candidates),
        'generated_rows': len(new_rows),
        'skipped_existing': skipped_existing,
        'skipped_status': skipped_status,
        'report_version': 1,
        'source_mode': source_mode,
        'output_file': str(DRY_RUN_REPORT),
        'rows_preview': [
            {
                'approval_id': row[approval_id_idx],
                'lead_id': row[lead_id_idx],
                'company_name': _field(row, idx, 'company_name'),
                'subject_or_hook': row[subject_idx],
                'status': row[status_idx],
                'notes': _field(row, idx, 'notes'),
            }
            for row in new_rows[:10]
        ],
    }
    _write_report(report)

    if args.dry_run:
        print({'mode': 'dry_run', 'new_rows': len(new_rows), 'report': str(DRY_RUN_REPORT)})
        return 0

    updated = approvals_rows + new_rows
    sheets.spreadsheets().values().update(
        spreadsheetId=CRM_SHEET_ID,
        range='Approvals!A1',
        valueInputOption='RAW',
        body={'values': updated},
    ).execute()

    # Agent logs writeback
    logs = read_sheet_rows(sheets, 'Agent_Logs')
    if logs:
        h = logs[0]
        i = {c: n for n, c in enumerate(h)}
        log_row = [''] * len(h)
        if 'timestamp' in i:
            log_row[i['timestamp']] = now()
        if 'agent' in i:
            log_row[i['agent']] = 'DraftGenerator'
        if 'activity' in i:
            log_row[i['activity']] = f'generated_approvals:{len(new_rows)}'
        if 'state' in i:
            log_row[i['state']] = 'completed'
        if 'notes' in i:
            log_row[i['notes']] = 'Approvals-only generation. No send path.'
        logs.append(log_row)
        sheets.spreadsheets().values().update(
            spreadsheetId=CRM_SHEET_ID,
            range='Agent_Logs!A1',
            valueInputOption='RAW',
            body={'values': logs},
        ).execute()

    # Keep cockpit data in sync after live writes.
    dashboard = __import__('generate_dashboard_data')
    payload = dashboard._live_to_dashboard()
    payload['source'] = {
        'mode_requested': 'live',
        'mode_resolved': 'live',
        'fallback_reason': None,
        'generated_at': now(),
        'sample_fallback_labeled': False,
        'badge': 'LIVE',
    }
    dashboard.OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding='utf-8')

    print({'mode': 'live', 'generated_rows': len(new_rows), 'report': str(DRY_RUN_REPORT)})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
