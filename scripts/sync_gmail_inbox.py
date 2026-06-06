#!/usr/bin/env python3
"""Read-only Gmail watcher for sponsorosops@gmail.com with classification fields."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from sponsoros_google import CRM_SHEET_ID, build_gmail_service, build_sheets_service, read_sheet_rows, rows_to_dicts

ROOT = Path(__file__).resolve().parent.parent
DRY_RUN_PATH = ROOT / 'data' / 'gmail_inbox_dry_run.json'
GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
SHEETS_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'

INBOX_HEADERS = [
    'inbox_id', 'thread_id', 'from_email', 'from_name', 'subject', 'snippet', 'status', 'priority', 'received_at',
    'needs_response', 'intent_category', 'thread_summary', 'mapped_lead_id', 'mapped_campaign_id', 'notes'
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _header(headers: list[dict[str, str]], name: str) -> str:
    for h in headers:
        if h.get('name', '').lower() == name.lower():
            return h.get('value', '')
    return ''


def _parse_from(value: str) -> tuple[str, str]:
    if '<' in value and '>' in value:
        left, right = value.split('<', 1)
        return right.split('>', 1)[0].strip().lower(), left.strip().strip('"')
    return value.strip().lower(), ''


def classify(subject: str, snippet: str) -> tuple[str, str, str, str]:
    text = f"{subject} {snippet}".lower()
    if any(k in text for k in ['not interested', 'unsubscribe', 'remove me']):
        return 'no', 'opt_out', 'Decline/opt-out signal detected.', 'closed'
    if any(k in text for k in ['price', 'budget', 'rate card', 'cost']):
        return 'yes', 'pricing', 'Asking about pricing or budget.', 'needs_reply'
    if any(k in text for k in ['call', 'meeting', 'schedule', 'availability']):
        return 'yes', 'meeting', 'Scheduling intent detected.', 'needs_reply'
    if any(k in text for k in ['thanks', 'received', 'looks good']):
        return 'no', 'ack', 'Acknowledgement without explicit ask.', 'read'
    return 'yes', 'general', 'General inbound requiring triage.', 'new'


def _gmail_messages(limit: int, lead_map: dict[str, str], campaign_map: dict[str, str]) -> list[dict[str, str]]:
    gmail = build_gmail_service([GMAIL_SCOPE])
    resp = gmail.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=limit).execute()
    rows = []
    for item in resp.get('messages', []):
        full = gmail.users().messages().get(userId='me', id=item['id'], format='metadata', metadataHeaders=['From', 'Subject', 'Date']).execute()
        headers = full.get('payload', {}).get('headers', [])
        from_email, from_name = _parse_from(_header(headers, 'From'))
        subject = _header(headers, 'Subject')
        snippet = full.get('snippet', '')
        received_at = ''
        date_raw = _header(headers, 'Date')
        if date_raw:
            try:
                received_at = parsedate_to_datetime(date_raw).astimezone(timezone.utc).isoformat()
            except Exception:
                received_at = ''

        needs_response, intent, summary, status = classify(subject, snippet)
        mapped_lead = ''
        mapped_campaign = ''
        text = f"{from_email} {from_name} {subject}".lower()
        for k, v in lead_map.items():
            if k and k in text:
                mapped_lead = v
                break
        for k, v in campaign_map.items():
            if k and k in text:
                mapped_campaign = v
                break

        rows.append({
            'inbox_id': full.get('id', ''),
            'thread_id': full.get('threadId', ''),
            'from_email': from_email,
            'from_name': from_name,
            'subject': subject,
            'snippet': snippet,
            'status': status,
            'priority': 'high' if needs_response == 'yes' else 'normal',
            'received_at': received_at,
            'needs_response': needs_response,
            'intent_category': intent,
            'thread_summary': summary,
            'mapped_lead_id': mapped_lead,
            'mapped_campaign_id': mapped_campaign,
            'notes': 'synced_readonly',
        })
    return rows


def _upsert(existing_rows: list[list[str]], new_rows: list[dict[str, str]]) -> list[list[str]]:
    headers = existing_rows[0] if existing_rows else INBOX_HEADERS
    if headers[:len(INBOX_HEADERS)] != INBOX_HEADERS:
        headers = INBOX_HEADERS
        existing_data = []
    else:
        existing_data = existing_rows[1:]
    idx = {h: i for i, h in enumerate(headers)}
    by_id = {}
    for row in existing_data:
        full = row + [''] * (len(headers) - len(row))
        key = full[idx['inbox_id']]
        if key:
            by_id[key] = full

    for item in new_rows:
        row = by_id.get(item['inbox_id'], [''] * len(headers))
        for k, v in item.items():
            if k in idx:
                row[idx[k]] = v
        by_id[item['inbox_id']] = row

    ordered = sorted(by_id.values(), key=lambda r: r[idx['received_at']], reverse=True)
    return [headers] + ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=25)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    lead_map = {}
    campaign_map = {}
    try:
        sheets_ro = build_sheets_service([SHEETS_SCOPE])
        lead_rows = rows_to_dicts(read_sheet_rows(sheets_ro, 'Leads'))
        for r in lead_rows:
            name = (r.get('company_name') or '').lower()
            dom = (r.get('website') or '').lower()
            if name:
                lead_map[name] = r.get('lead_id', '')
            if dom:
                lead_map[dom.replace('https://', '').replace('http://', '').replace('www.', '')] = r.get('lead_id', '')
        for r in rows_to_dicts(read_sheet_rows(sheets_ro, 'Campaigns')):
            n = (r.get('campaign_name') or '').lower()
            if n:
                campaign_map[n] = r.get('campaign_id', '')
    except Exception:
        pass

    try:
        inbox_rows = _gmail_messages(args.limit, lead_map, campaign_map)
    except Exception as exc:
        DRY_RUN_PATH.write_text(json.dumps({'mode': 'dry_run', 'reason': f'gmail_readonly_unavailable:{type(exc).__name__}', 'generated_at': utc_now(), 'messages': []}, indent=2), encoding='utf-8')
        print(f'Wrote dry-run {DRY_RUN_PATH}')
        return 0

    if args.dry_run:
        DRY_RUN_PATH.write_text(json.dumps({'mode': 'dry_run_forced', 'generated_at': utc_now(), 'messages': inbox_rows}, indent=2), encoding='utf-8')
        print(f'Wrote dry-run {DRY_RUN_PATH}')
        return 0

    try:
        sheets = build_sheets_service([SHEETS_SCOPE])
        existing = read_sheet_rows(sheets, 'Inbox')
        merged = _upsert(existing, inbox_rows)
        sheets.spreadsheets().values().update(
            spreadsheetId=CRM_SHEET_ID,
            range='Inbox!A1',
            valueInputOption='RAW',
            body={'values': merged},
        ).execute()
        print(f'Updated Inbox tab with {len(inbox_rows)} messages')
        return 0
    except Exception as exc:
        DRY_RUN_PATH.write_text(json.dumps({'mode': 'dry_run', 'reason': f'sheets_write_unavailable:{type(exc).__name__}', 'generated_at': utc_now(), 'messages': inbox_rows}, indent=2), encoding='utf-8')
        print(f'Wrote dry-run {DRY_RUN_PATH}')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
