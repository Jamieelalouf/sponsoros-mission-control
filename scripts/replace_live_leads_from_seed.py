#!/usr/bin/env python3
"""Replace live Leads tab with the cleaned real lead seed JSON."""
from __future__ import annotations
import json
from pathlib import Path
from sponsoros_google import CRM_SHEET_ID, build_sheets_service, read_sheet_rows

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / 'data' / 'real_lead_seed_web_search.json'
SCOPE = 'https://www.googleapis.com/auth/spreadsheets'


def main() -> int:
    payload = json.loads(SEED.read_text(encoding='utf-8'))
    leads = payload.get('leads', [])
    if len(leads) < 1:
        raise SystemExit('No seed leads found')
    sheets = build_sheets_service([SCOPE])
    rows = read_sheet_rows(sheets, 'Leads')
    if not rows:
        raise SystemExit('Leads tab empty')
    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}
    out = [headers]
    for lead in leads:
        row = [''] * len(headers)
        mappings = {
            'lead_id': lead.get('lead_id',''),
            'company_name': lead.get('company_name',''),
            'website': lead.get('website',''),
            'industry': lead.get('industry') or lead.get('category',''),
            'location': lead.get('location',''),
            'source': lead.get('source',''),
            'source_url': lead.get('source_url',''),
            'fit_score': str(lead.get('fit_score','')),
            'status': lead.get('status','Proposed'),
            'owner': 'Scout',
            'priority': 'high' if int(lead.get('fit_score',0)) >= 75 else 'medium',
            'notes': f"confidence={lead.get('confidence','')}; discovered_at={lead.get('discovered_at','')}; {lead.get('notes','')}"[:450],
            'created_at': lead.get('created_at',''),
            'updated_at': lead.get('updated_at',''),
        }
        for k,v in mappings.items():
            if k in idx:
                row[idx[k]] = v
        out.append(row)
    sheets.spreadsheets().values().clear(spreadsheetId=CRM_SHEET_ID, range='Leads!A:ZZ', body={}).execute()
    sheets.spreadsheets().values().update(spreadsheetId=CRM_SHEET_ID, range='Leads!A1', valueInputOption='RAW', body={'values': out}).execute()
    print({'written': len(leads)})
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
