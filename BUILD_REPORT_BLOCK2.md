# SponsorOS MVP Block 2 Build Report

Generated: 2026-05-14 (local)
Project: `/Users/clawd/sponsoros-mission-control`

## Scope Implemented

Implemented all requested Block 2 scaffolding/features in clean-room SponsorOS with strict `HERMES_HOME=/Users/clawd/.hermes-sponsoros` usage for live Google access paths.

## What Was Built

1. Real Scout pipeline (`scripts/scout_pipeline.py`)
- Commands: `discover`, `enrich`, `dedupe`, `score`, `dry-run`, `write-live`
- Public discovery strategy:
  - Preferred: Google Maps Places Text Search when `GOOGLE_MAPS_API_KEY` or `GMAPS_API_KEY` exists
  - Fallback: DuckDuckGo public JSON endpoint (safe static HTTP)
- Lead fields include: `source_url`, `website/domain`, `location`, `category`, `status`, `fit_score`, `confidence`, `notes`, `discovered_at`
- Dedupe against live `Leads/Companies/Contacts` by normalized name+domain (fails open to empty keyset if offline)
- Explicit live write only via `npm run scout:write-live`
- Dry-run default output: `data/dry_run_scout_enricher.json`
- Structured shortage reason when 50 cannot be verified in run

2. Scout/Enricher modular pipeline scripts
- `scripts/scout_pipeline.py`
- Backward wrapper updated: `scripts/run_scout_enricher.py`
- Agent log writeback on live write path

3. Approval cockpit UI (local)
- `public/approval-cockpit.html`
- Prominent `ZERO SEND PATH / approval only` marker
- Local edit/save/export flow
- CLI sync path: `npm run approvals:sync-local` (`scripts/approval_cockpit.py`)

4. Locked draft generation to Approvals only
- `scripts/generate_approval_drafts.py`
- Writes only to `Approvals`
- Verifies `sent_at` blank and status in `Pending/Edited`
- No Gmail draft usage

5. Inbox watcher polish
- `scripts/sync_gmail_inbox.py` adds:
  - `needs_response`
  - `intent_category`
  - `thread_summary`
  - `mapped_lead_id`
  - `mapped_campaign_id`
- Gmail remains read-only (`gmail.readonly`), no modify calls

6. Dashboard polish
- `index.html` redesigned with executive cards and source badge
- `public/standalone-preview.html` mirrored
- `scripts/generate_dashboard_data.py` now emits source badge and executive metrics
- Action links to approval cockpit and preview routes

7. Python/runtime cleanup
- `scripts/python_runner.py` prefers:
  - `/Users/clawd/.hermes/hermes-agent/venv/bin/python`
  - fallback to current python executable
- `package.json` scripts updated to use runner

8. Daily Operator scaffold
- `scripts/daily_operator.py`
- Runs refresh sequence: scout dry-run, gmail sync, dashboard generate, local report
- Optional scout live write only when explicitly requested with flag
- No cron creation

## Verification Commands Run

1. `npm run verify`  
Result: PASS

2. `HERMES_HOME=/Users/clawd/.hermes-sponsoros npm run verify:crm`  
Result: BLOCKED (network/DNS to `oauth2.googleapis.com` unavailable in current environment)

3. `npm run verify:no-send`  
Result: PASS (`no send/modify gmail paths found`)

4. `npm run verify:live-state`  
Result: BLOCKED (same network/DNS constraint)

5. `npm run scout:dry-run`  
Result: BLOCKED on live dedupe lookup due Google token refresh DNS; pipeline patched to fail-open dedupe in dry-run path and pass in `npm run verify`

6. `npm run generate:live`  
Result: BLOCKED (same network/DNS constraint)

7. Obsidian report path check: `ls -la /Users/clawd/Obsidian ...`  
Result: path not found; report written locally instead

## Dry-Run Scout Output

- File: `data/dry_run_scout_enricher.json`
- Current run in this environment: `verified_count=0`
- Contains structured shortage reason because safe public discovery + live verification were constrained by network/API availability.

## Live Verification Status

- Live CRM and live dashboard verification are implemented, but could not be executed end-to-end due DNS/network restrictions resolving Google OAuth host in this runtime.

## Key Files Added/Updated

- `scripts/scout_pipeline.py`
- `scripts/run_scout_enricher.py`
- `scripts/generate_approval_drafts.py`
- `scripts/sync_gmail_inbox.py`
- `scripts/generate_dashboard_data.py`
- `scripts/approval_cockpit.py`
- `scripts/daily_operator.py`
- `scripts/python_runner.py`
- `scripts/verify_scout_output.py`
- `scripts/verify_dashboard_route.py`
- `scripts/verify_live_crm_state.py`
- `scripts/verify_all.py`
- `public/approval-cockpit.html`
- `index.html`
- `public/standalone-preview.html`
- `package.json`
- `README.md`
- `BUILD_REPORT_BLOCK2.md`

