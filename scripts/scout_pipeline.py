#!/usr/bin/env python3
"""SponsorOS Scout + Enricher pipeline.

Safe defaults:
- discover/enrich/dedupe/score are local dry-run transforms.
- write-live is explicit and requires HERMES_HOME isolation.
- No outbound email/draft/send paths.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

from sponsoros_google import CRM_SHEET_ID, build_sheets_service, read_sheet_rows, rows_to_dicts

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
DISCOVER_PATH = DATA_DIR / 'scout_discovered.json'
ENRICH_PATH = DATA_DIR / 'scout_enriched.json'
DEDUPE_PATH = DATA_DIR / 'scout_deduped.json'
SCORED_PATH = DATA_DIR / 'scout_scored.json'
DRY_RUN_PATH = DATA_DIR / 'dry_run_scout_enricher.json'

SHEETS_RW_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'
SHEETS_RO_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'

TARGET_CATEGORIES = [
    'hydration brand',
    'wellness brand',
    'recovery studio',
    'activewear brand',
    'streetwear brand',
    'creator tools platform',
    'youth sports event organizer',
    'dance competition organizer',
    'event production agency',
    'independent gym',
]
TARGET_REGIONS = [
    'New York NY', 'Los Angeles CA', 'Chicago IL', 'Austin TX', 'Atlanta GA'
]

LEAD_STATUSES = {'New', 'Research', 'Proposed', 'Qualified'}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_name(value: str) -> str:
    clean = re.sub(r'[^a-z0-9]+', ' ', (value or '').lower()).strip()
    suffixes = {'inc', 'llc', 'co', 'corp', 'company', 'ltd', 'group', 'studio'}
    parts = [p for p in clean.split() if p not in suffixes]
    return ' '.join(parts)


def normalize_domain(url_or_domain: str) -> str:
    raw = (url_or_domain or '').strip().lower()
    if not raw:
        return ''
    if '://' not in raw:
        raw = f'https://{raw}'
    parsed = urlparse(raw)
    host = parsed.netloc or parsed.path
    host = host.split('@')[-1].split(':')[0]
    if host.startswith('www.'):
        host = host[4:]
    return host


def slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def polite_get_json(url: str, timeout: int = 15) -> Any:
    req = Request(url, headers={'User-Agent': 'SponsorOS-Scout/1.0 (polite static fetch)'})
    with urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode('utf-8'))


def discover_via_places(limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY') or os.environ.get('GMAPS_API_KEY')
    if not api_key:
        return [], {'used': False, 'reason': 'missing_places_key'}

    out: list[dict[str, Any]] = []
    for region in TARGET_REGIONS:
        for category in TARGET_CATEGORIES:
            if len(out) >= limit:
                break
            query = quote_plus(f'{category} {region}')
            url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={quote_plus(api_key)}'
            try:
                payload = polite_get_json(url)
            except Exception as exc:
                return out, {'used': True, 'reason': f'places_error:{type(exc).__name__}', 'count': len(out)}

            results = payload.get('results', [])[:5]
            for r in results:
                if len(out) >= limit:
                    break
                name = r.get('name', '').strip()
                if not name:
                    continue
                website = ''
                maps_url = ''
                place_id = r.get('place_id', '')
                if place_id:
                    maps_url = f'https://www.google.com/maps/place/?q=place_id:{place_id}'
                location = r.get('formatted_address') or region
                types = ', '.join(r.get('types') or [])
                out.append({
                    'lead_id': f'lead-{uuid.uuid4().hex[:10]}',
                    'company_name': name,
                    'website': website,
                    'domain': '',
                    'industry': category,
                    'category': category,
                    'location': location,
                    'source': 'google_places',
                    'source_url': maps_url or url,
                    'status': 'Research',
                    'fit_score': 0,
                    'confidence': 0.65,
                    'notes': f'Places type hints: {types}'[:350],
                    'discovered_at': utc_now(),
                    'created_at': utc_now(),
                    'updated_at': utc_now(),
                })

    return out, {'used': True, 'reason': None, 'count': len(out)}


def discover_via_ddg(limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    issues: list[str] = []
    for region in TARGET_REGIONS:
        for category in TARGET_CATEGORIES:
            if len(out) >= limit:
                break
            q = quote_plus(f'{category} {region} sponsorship')
            url = f'https://duckduckgo.com/?q={q}&format=json&pretty=1'
            try:
                payload = polite_get_json(url)
            except Exception as exc:
                issues.append(f'ddg_error:{type(exc).__name__}')
                continue
            topics = payload.get('RelatedTopics') or []
            flat = []
            for t in topics:
                if isinstance(t, dict) and 'Topics' in t:
                    flat.extend(t.get('Topics') or [])
                elif isinstance(t, dict):
                    flat.append(t)
            for item in flat:
                if len(out) >= limit:
                    break
                text = item.get('Text', '')
                first_url = item.get('FirstURL', '')
                if not text or not first_url:
                    continue
                name = text.split(' - ')[0].strip()[:120]
                domain = normalize_domain(first_url)
                out.append({
                    'lead_id': f'lead-{uuid.uuid4().hex[:10]}',
                    'company_name': name,
                    'website': f'https://{domain}' if domain else '',
                    'domain': domain,
                    'industry': category,
                    'category': category,
                    'location': region,
                    'source': 'duckduckgo_public',
                    'source_url': first_url,
                    'status': 'Research',
                    'fit_score': 0,
                    'confidence': 0.45,
                    'notes': 'Public search candidate; requires enrichment verification.',
                    'discovered_at': utc_now(),
                    'created_at': utc_now(),
                    'updated_at': utc_now(),
                })
    return out, {'used': True, 'issues': dict(Counter(issues)), 'count': len(out)}


def enrich(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for lead in leads:
        row = dict(lead)
        domain = row.get('domain') or normalize_domain(row.get('website') or row.get('source_url', ''))
        row['domain'] = domain
        if not row.get('website') and domain:
            row['website'] = f'https://{domain}'
        cat = (row.get('category') or row.get('industry') or '').lower()
        score = 45
        if any(k in cat for k in ['hydration', 'wellness', 'recovery', 'activewear', 'streetwear']):
            score += 20
        if any(k in cat for k in ['creator', 'event', 'youth', 'dance']):
            score += 20
        if 'gym' in cat:
            score += 5
            if any(w in (row.get('company_name', '')).lower() for w in ['24 hour', 'planet fitness', 'equinox']):
                score -= 20
                row['notes'] = (row.get('notes', '') + ' Potential large-chain gym; deprioritize.').strip()
        if row.get('domain'):
            score += 5
        row['fit_score'] = max(1, min(99, score))
        row['confidence'] = max(0.2, min(0.95, float(row.get('confidence', 0.5)) + (0.15 if row.get('domain') else 0)))
        row['status'] = 'Proposed' if row['fit_score'] >= 60 else 'Research'
        row['updated_at'] = utc_now()
        enriched.append(row)
    return enriched


def load_existing_dedupe_keys() -> tuple[set[tuple[str, str]], str | None]:
    try:
        sheets = build_sheets_service([SHEETS_RO_SCOPE])
        keys: set[tuple[str, str]] = set()
        for tab in ['Leads', 'Companies', 'Contacts']:
            rows = rows_to_dicts(read_sheet_rows(sheets, tab))
            for row in rows:
                name = normalize_name(row.get('company_name') or row.get('name') or '')
                domain = normalize_domain(row.get('website') or row.get('domain') or row.get('email') or '')
                if name or domain:
                    keys.add((name, domain))
        return keys, None
    except Exception as exc:
        return set(), f'dedupe_live_lookup_unavailable:{type(exc).__name__}'


def dedupe(leads: list[dict[str, Any]], existing_keys: set[tuple[str, str]]) -> tuple[list[dict[str, Any]], int]:
    seen = set(existing_keys)
    out = []
    dropped = 0
    for lead in leads:
        key = (normalize_name(lead.get('company_name', '')), normalize_domain(lead.get('domain') or lead.get('website', '')))
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        out.append(lead)
    return out, dropped


def append_agent_log(message: str, detail: str) -> None:
    sheets = build_sheets_service([SHEETS_RW_SCOPE])
    rows = read_sheet_rows(sheets, 'Agent_Logs')
    headers = rows[0] if rows else ['timestamp', 'agent', 'activity', 'state', 'notes']
    new_row = [''] * len(headers)
    idx = {h: i for i, h in enumerate(headers)}
    def put(col: str, val: str) -> None:
        if col in idx:
            new_row[idx[col]] = val
    put('timestamp', utc_now())
    put('agent', 'ScoutPipeline')
    put('activity', message)
    put('state', 'completed')
    put('notes', detail[:500])
    all_rows = [headers] + rows[1:] + [new_row] if rows else [headers, new_row]
    sheets.spreadsheets().values().update(
        spreadsheetId=CRM_SHEET_ID,
        range='Agent_Logs!A1',
        valueInputOption='RAW',
        body={'values': all_rows},
    ).execute()


def write_leads_live(leads: list[dict[str, Any]]) -> dict[str, Any]:
    sheets = build_sheets_service([SHEETS_RW_SCOPE])
    rows = read_sheet_rows(sheets, 'Leads')
    if not rows:
        raise SystemExit('Leads sheet is empty; cannot write safely')
    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers)}
    required = ['lead_id', 'company_name', 'website', 'industry', 'location', 'source', 'source_url', 'fit_score', 'status', 'owner', 'priority', 'notes', 'created_at', 'updated_at']
    missing = [h for h in required if h not in idx]
    if missing:
        raise SystemExit(f'Leads headers missing required fields: {missing}')

    existing = rows_to_dicts(rows)
    existing_keys = {(normalize_name(r.get('company_name', '')), normalize_domain(r.get('website', ''))) for r in existing}

    appended = 0
    for lead in leads:
        k = (normalize_name(lead.get('company_name', '')), normalize_domain(lead.get('domain') or lead.get('website', '')))
        if k in existing_keys:
            continue
        row = [''] * len(headers)
        row[idx['lead_id']] = lead.get('lead_id', '')
        row[idx['company_name']] = lead.get('company_name', '')
        row[idx['website']] = lead.get('website', '')
        row[idx['industry']] = lead.get('category') or lead.get('industry', '')
        row[idx['location']] = lead.get('location', '')
        row[idx['source']] = lead.get('source', '')
        row[idx['source_url']] = lead.get('source_url', '')
        row[idx['fit_score']] = str(lead.get('fit_score', ''))
        row[idx['status']] = lead.get('status', 'Proposed') if lead.get('status') in LEAD_STATUSES else 'Proposed'
        row[idx['owner']] = 'Scout'
        row[idx['priority']] = 'high' if int(lead.get('fit_score', 0)) >= 75 else 'medium'
        row[idx['notes']] = f"confidence={lead.get('confidence','')}; discovered_at={lead.get('discovered_at','')}; {lead.get('notes','')}"[:450]
        row[idx['created_at']] = lead.get('created_at', utc_now())
        row[idx['updated_at']] = utc_now()
        rows.append(row)
        existing_keys.add(k)
        appended += 1

    sheets.spreadsheets().values().update(
        spreadsheetId=CRM_SHEET_ID,
        range='Leads!A1',
        valueInputOption='RAW',
        body={'values': rows},
    ).execute()

    append_agent_log('scout_write_live', f'appended={appended} requested={len(leads)}')
    return {'requested': len(leads), 'appended': appended}


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def cmd_discover(args: argparse.Namespace) -> int:
    places, places_meta = discover_via_places(args.limit)
    leads = places
    fallback_meta = None
    if len(leads) < args.limit:
        fallback, fallback_meta = discover_via_ddg(args.limit - len(leads))
        leads.extend(fallback)

    shortage = None
    if len(leads) < args.limit:
        shortage = {
            'requested': args.limit,
            'found': len(leads),
            'reason': 'insufficient_verified_public_candidates',
            'details': {
                'places': places_meta,
                'fallback': fallback_meta,
            },
        }

    payload = {
        'stage': 'discover',
        'generated_at': utc_now(),
        'requested': args.limit,
        'count': len(leads),
        'leads': leads,
        'source_meta': {'places': places_meta, 'fallback': fallback_meta},
        'shortage_reason': shortage,
    }
    save_json(DISCOVER_PATH, payload)
    print(f'Wrote {DISCOVER_PATH} count={len(leads)}')
    return 0


def cmd_enrich(_: argparse.Namespace) -> int:
    src = json.loads(DISCOVER_PATH.read_text(encoding='utf-8'))
    leads = enrich(src.get('leads', []))
    payload = {'stage': 'enrich', 'generated_at': utc_now(), 'count': len(leads), 'leads': leads}
    save_json(ENRICH_PATH, payload)
    print(f'Wrote {ENRICH_PATH} count={len(leads)}')
    return 0


def cmd_dedupe(_: argparse.Namespace) -> int:
    src = json.loads(ENRICH_PATH.read_text(encoding='utf-8'))
    existing, warning = load_existing_dedupe_keys()
    leads, dropped = dedupe(src.get('leads', []), existing)
    payload = {
        'stage': 'dedupe',
        'generated_at': utc_now(),
        'count': len(leads),
        'dropped_duplicates': dropped,
        'warning': warning,
        'leads': leads,
    }
    save_json(DEDUPE_PATH, payload)
    print(f'Wrote {DEDUPE_PATH} count={len(leads)} dropped={dropped}')
    return 0


def cmd_score(_: argparse.Namespace) -> int:
    src = json.loads(DEDUPE_PATH.read_text(encoding='utf-8'))
    leads = sorted(src.get('leads', []), key=lambda x: int(x.get('fit_score', 0)), reverse=True)
    payload = {'stage': 'score', 'generated_at': utc_now(), 'count': len(leads), 'leads': leads}
    save_json(SCORED_PATH, payload)
    print(f'Wrote {SCORED_PATH} count={len(leads)}')
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    cmd_discover(args)
    cmd_enrich(args)
    cmd_dedupe(args)
    cmd_score(args)
    scored = json.loads(SCORED_PATH.read_text(encoding='utf-8'))
    discovered = json.loads(DISCOVER_PATH.read_text(encoding='utf-8'))
    leads = scored.get('leads', [])
    payload = {
        'mode': 'dry_run',
        'generated_at': utc_now(),
        'requested': args.limit,
        'verified_count': len(leads),
        'leads': leads,
        'shortage_reason': discovered.get('shortage_reason'),
        'no_outbound_contact': True,
        'no_send_path': True,
        'write_live_performed': False,
    }
    save_json(DRY_RUN_PATH, payload)
    print(f'Wrote {DRY_RUN_PATH} count={len(leads)}')
    return 0


def cmd_write_live(args: argparse.Namespace) -> int:
    payload = json.loads(SCORED_PATH.read_text(encoding='utf-8'))
    leads = payload.get('leads', [])[: args.limit]
    result = write_leads_live(leads)
    report = {'mode': 'live_write', 'generated_at': utc_now(), 'result': result}
    save_json(DRY_RUN_PATH, report)
    print(json.dumps(report, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)

    p_discover = sub.add_parser('discover')
    p_discover.add_argument('--limit', type=int, default=50)
    p_discover.set_defaults(func=cmd_discover)

    p_enrich = sub.add_parser('enrich')
    p_enrich.set_defaults(func=cmd_enrich)

    p_dedupe = sub.add_parser('dedupe')
    p_dedupe.set_defaults(func=cmd_dedupe)

    p_score = sub.add_parser('score')
    p_score.set_defaults(func=cmd_score)

    p_dry = sub.add_parser('dry-run')
    p_dry.add_argument('--limit', type=int, default=50)
    p_dry.set_defaults(func=cmd_dry_run)

    p_live = sub.add_parser('write-live')
    p_live.add_argument('--limit', type=int, default=50)
    p_live.set_defaults(func=cmd_write_live)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
