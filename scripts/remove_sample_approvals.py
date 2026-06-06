#!/usr/bin/env python3
"""Remove sample/demo rows from SponsorOS live Approvals tab."""
from __future__ import annotations

from sponsoros_google import CRM_SHEET_ID, build_sheets_service, read_sheet_rows

SCOPE = 'https://www.googleapis.com/auth/spreadsheets'


def main() -> int:
    sheets = build_sheets_service([SCOPE])
    rows = read_sheet_rows(sheets, 'Approvals')
    if not rows:
        raise SystemExit('Approvals tab empty')
    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}

    def cell(row: list[str], name: str) -> str:
        i = idx.get(name)
        return row[i] if i is not None and i < len(row) else ''

    kept = [headers]
    removed = 0
    for row in rows[1:]:
        haystack = ' '.join([
            cell(row, 'approval_id'),
            cell(row, 'lead_id'),
            cell(row, 'company_name'),
            cell(row, 'draft_body'),
            cell(row, 'notes'),
        ]).lower()
        if (
            'appr_demo' in haystack
            or 'lead_demo' in haystack
            or 'sample dry-run approval' in haystack
            or 'sample copy only' in haystack
        ):
            removed += 1
            continue
        kept.append(row + [''] * (len(headers) - len(row)))

    sheets.spreadsheets().values().clear(
        spreadsheetId=CRM_SHEET_ID,
        range='Approvals!A:ZZ',
        body={},
    ).execute()
    sheets.spreadsheets().values().update(
        spreadsheetId=CRM_SHEET_ID,
        range='Approvals!A1',
        valueInputOption='RAW',
        body={'values': kept},
    ).execute()
    print({'removed': removed, 'remaining': len(kept) - 1})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
