#!/usr/bin/env python3
"""Approval cockpit CLI for local and CRM approval editing.

No send actions exist in this script.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sponsoros_google import CRM_SHEET_ID, build_sheets_service, read_sheet_rows

ROOT = Path(__file__).resolve().parent.parent
LOCAL_APPROVALS = ROOT / 'data' / 'approval_edits.json'
ALLOWED_STATUSES = {'Pending', 'Edited', 'Approved', 'Rejected'}


def _ensure_local_file() -> list[dict[str, str]]:
    if not LOCAL_APPROVALS.exists():
        LOCAL_APPROVALS.write_text('[]\n', encoding='utf-8')
    return json.loads(LOCAL_APPROVALS.read_text(encoding='utf-8'))


def _save_local(items: list[dict[str, str]]) -> None:
    LOCAL_APPROVALS.write_text(json.dumps(items, indent=2) + '\n', encoding='utf-8')


def local_list() -> int:
    print(json.dumps({'count': len(_ensure_local_file()), 'items': _ensure_local_file()}, indent=2))
    return 0


def local_upsert(approval_id: str, status: str, subject: str | None, draft_body: str | None, notes: str | None) -> int:
    if status not in ALLOWED_STATUSES:
        raise SystemExit(f'Invalid status {status}. Allowed: {sorted(ALLOWED_STATUSES)}')
    items = _ensure_local_file()
    by_id = {i.get('approval_id'): i for i in items}
    item = by_id.get(approval_id, {'approval_id': approval_id})
    item['status'] = status
    if subject is not None:
        item['subject_or_hook'] = subject
    if draft_body is not None:
        item['draft_body'] = draft_body
    if notes is not None:
        item['notes'] = notes
    by_id[approval_id] = item
    _save_local(list(by_id.values()))
    print(json.dumps(item, indent=2))
    return 0


def _crm_update_single(sheets, approval_id: str, status: str, subject: str | None, draft_body: str | None, notes: str | None) -> int:
    rows = read_sheet_rows(sheets, 'Approvals')
    if not rows:
        raise SystemExit('Approvals sheet is empty')
    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}
    for req in ['approval_id', 'status']:
        if req not in idx:
            raise SystemExit(f'Missing required column: {req}')

    target = None
    for i, row in enumerate(rows[1:], start=2):
        if row and row[0] == approval_id:
            target = i
            break
    if target is None:
        return 0

    values = rows[target - 1] + [''] * (len(headers) - len(rows[target - 1]))
    values[idx['status']] = status
    if subject is not None and 'subject_or_hook' in idx:
        values[idx['subject_or_hook']] = subject
    if draft_body is not None and 'draft_body' in idx:
        values[idx['draft_body']] = draft_body
    if notes is not None and 'notes' in idx:
        values[idx['notes']] = notes

    end_col = chr(ord('A') + len(headers) - 1)
    sheets.spreadsheets().values().update(
        spreadsheetId=CRM_SHEET_ID,
        range=f'Approvals!A{target}:{end_col}{target}',
        valueInputOption='RAW',
        body={'values': [values]},
    ).execute()
    return 1


def crm_update(approval_id: str, status: str, subject: str | None, draft_body: str | None, notes: str | None) -> int:
    if status not in ALLOWED_STATUSES:
        raise SystemExit(f'Invalid status {status}. Allowed: {sorted(ALLOWED_STATUSES)}')
    sheets = build_sheets_service(['https://www.googleapis.com/auth/spreadsheets'])
    updated = _crm_update_single(sheets, approval_id, status, subject, draft_body, notes)
    if not updated:
        raise SystemExit(f'Approval id not found: {approval_id}')
    print(json.dumps({'approval_id': approval_id, 'status': status, 'updated': True}, indent=2))
    return 0


def sync_local_to_crm() -> int:
    items = _ensure_local_file()
    sheets = build_sheets_service(['https://www.googleapis.com/auth/spreadsheets'])
    updated = 0
    for item in items:
        status = item.get('status', 'Pending')
        if status not in ALLOWED_STATUSES:
            continue
        updated += _crm_update_single(
            sheets,
            item.get('approval_id', ''),
            status,
            item.get('subject_or_hook'),
            item.get('draft_body'),
            item.get('notes'),
        )
    print(json.dumps({'synced_from_local': len(items), 'updated_rows': updated}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list-local')
    up = sub.add_parser('upsert-local')
    up.add_argument('--approval-id', required=True)
    up.add_argument('--status', required=True)
    up.add_argument('--subject')
    up.add_argument('--draft-body')
    up.add_argument('--notes')

    crm = sub.add_parser('update-crm')
    crm.add_argument('--approval-id', required=True)
    crm.add_argument('--status', required=True)
    crm.add_argument('--subject')
    crm.add_argument('--draft-body')
    crm.add_argument('--notes')

    sub.add_parser('sync-local-to-crm')

    args = parser.parse_args()
    if args.command == 'list-local':
        return local_list()
    if args.command == 'upsert-local':
        return local_upsert(args.approval_id, args.status, args.subject, args.draft_body, args.notes)
    if args.command == 'update-crm':
        return crm_update(args.approval_id, args.status, args.subject, args.draft_body, args.notes)
    if args.command == 'sync-local-to-crm':
        return sync_local_to_crm()
    raise SystemExit('Unknown command')


if __name__ == '__main__':
    raise SystemExit(main())
