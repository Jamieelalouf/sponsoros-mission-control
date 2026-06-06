# SponsorOS Mission Control (MVP Block 2)

Standalone local project for SponsorOS Mission Control with Scout/Enricher + approval-lock workflows.

## Hard Guardrails

- Clean-room only. Never use VISION/Jarvis credentials, data, or sheet IDs.
- Required isolation: `HERMES_HOME=/Users/clawd/.hermes-sponsoros`
- CRM Sheet ID is fixed to: `10IJPrZBE3JJoh7ePeslBeAY10yLxDT0WFaPUHoqPFwY`
- No email sends. No Gmail modify. No Gmail draft create/send.
- No public posting. No spending. No deploy. No commit.
- Approval generation writes to `Approvals` only and keeps `sent_at` blank.

## Block 2 Components

- `scripts/scout_pipeline.py`
  - `discover`: public discovery (`google_places` if key exists, else DuckDuckGo fallback)
  - `enrich`: domain normalization + confidence + fit scoring
  - `dedupe`: normalized name+domain against `Leads/Companies/Contacts`
  - `score`: rank by fit score
  - `dry-run`: end-to-end pipeline output in `data/dry_run_scout_enricher.json`
  - `write-live`: explicit live append to CRM Leads + Agent_Logs
- `scripts/generate_approval_drafts.py`: writes draft text into `Approvals` only; validates `status in Pending/Edited` and `sent_at=''`
- `scripts/sync_gmail_inbox.py`: read-only Gmail sync with `needs_response`, `intent_category`, `thread_summary`, `mapped_lead_id`, `mapped_campaign_id`
- `public/approval-cockpit.html`: local approval edit cockpit; clearly marked `ZERO SEND PATH / approval only`
- `scripts/approval_cockpit.py`: local JSON edits + explicit CRM sync command
- `scripts/daily_operator.py`: daily scaffold sequence (scout dry-run, gmail sync, dashboard generate, report)
- `scripts/python_runner.py`: prefers `/Users/clawd/.hermes/hermes-agent/venv/bin/python`, graceful fallback

## Commands

```bash
cd /Users/clawd/sponsoros-mission-control

# Dashboard
npm run generate
npm run generate:live

# Scout pipeline (default safe)
npm run scout:dry-run
npm run scout:discover
npm run scout:enrich
npm run scout:dedupe
npm run scout:score

# Explicit live write to CRM Leads
npm run scout:write-live

# Draft generation (Approvals only)
npm run drafts:approvals:dryrun
npm run drafts:approvals

# Inbox (read-only Gmail)
npm run gmail:dryrun
npm run gmail:sync

# Approval cockpit
npm run approvals:list
npm run approvals:edit
npm run approvals:sync-local

# Daily operator scaffold
npm run operator:daily

# Verification
npm run verify
npm run verify:crm
npm run verify:no-send
npm run verify:live-state

# Browser preview
npm run preview
# Routes:
# http://localhost:8080/index.html
# http://localhost:8080/public/approval-cockpit.html
# http://localhost:8080/public/standalone-preview.html
```

## Scout Output Expectations

`data/dry_run_scout_enricher.json` includes either:
- verified leads with required fields (`source_url`, `website/domain`, `location`, `category`, `status`, `fit_score`, `confidence`, `notes`, `discovered_at`), or
- `shortage_reason` with structured details when 50 leads cannot be safely verified in a run.

## Source Badge

Dashboard always labels data source in `data/dashboard.json > source`:
- `badge`: `LIVE` or `SAMPLE`
- `mode_resolved`: `live`, `sample`, or `sample_fallback`

