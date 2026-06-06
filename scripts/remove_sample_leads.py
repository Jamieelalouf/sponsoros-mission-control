#!/usr/bin/env python3
"""Remove sample/demo leads from the SponsorOS live Leads tab."""
from __future__ import annotations

from sponsoros_google import CRM_SHEET_ID, build_sheets_service, read_sheet_rows

SCOPE = 'https://www.googleapis.com/auth/spreadsheets'


def is_sample(row: list[str], idx: dict[str, int]) -> bool:
    def cell(name: str) -> str:
        i = idx.get(name)
        return row[i] if i is not None and i < len(row) else ''
    return (
        cell('source').lower() == 'sample'
        or cell('source_url').lower().startswith('sample://')
        or cell('lead_id').lower().startswith('lead_demo')
        or 'fake sample lead' in cell('notes').lower()
    )


def main() -> int:
    sheets = build_sheets_service([SCOPE])
    rows = read_sheet_rows(sheets, 'Leads')
    if not rows:
        raise SystemExit('Leads tab empty')
    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}
    kept = [headers]
    removed = 0
    for row in rows[1:]:
        full = row + [''] * (len(headers) - len(row))
        if is_sample(full, idx):
            removed += 1
            continue
        kept.append(full)

    # Clear first so stale tail rows disappear, then write compact table.
    sheets.spreadsheets().values().clear(
        spreadsheetId=CRM_SHEET_ID,
        range='Leads!A:ZZ',
        body={},
    ).execute()
    sheets.spreadsheets().values().update(
        spreadsheetId=CRM_SHEET_ID,
        range='Leads!A1',
        valueInputOption='RAW',
        body={'values': kept},
    ).execute()
    print({'removed': removed, 'remaining': len(kept) - 1})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
