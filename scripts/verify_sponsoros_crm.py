#!/usr/bin/env python3
"""Verify SponsorOS CRM tabs/headers using isolated SponsorOS OAuth.

Never prints secrets. Requires HERMES_HOME=/Users/clawd/.hermes-sponsoros.
"""
from __future__ import annotations

import json
import os

from sponsoros_google import CRM_SHEET_ID, REQUIRED_HERMES_HOME, build_sheets_service, read_sheet_rows

EXPECTED_TABS = [
    "Leads", "Companies", "Contacts", "Campaigns", "Approvals",
    "Inbox", "Sent_Log", "Agent_Logs", "Settings",
]
EXPECTED_HEADERS = {
    "Leads": ["lead_id", "company_name", "website", "industry", "location", "source", "source_url", "fit_score", "status", "owner", "priority", "notes", "created_at", "updated_at"],
    "Approvals": ["approval_id", "lead_id", "company_name", "contact_email", "channel", "subject_or_hook", "draft_body", "status", "approved_by", "approved_at", "sent_at", "notes", "created_at"],
    "Settings": ["key", "value", "notes"],
}


def main() -> int:
    if os.environ.get("HERMES_HOME") != REQUIRED_HERMES_HOME:
        raise SystemExit(f"Wrong HERMES_HOME. Expected {REQUIRED_HERMES_HOME}")

    service = build_sheets_service(["https://www.googleapis.com/auth/spreadsheets"])
    spreadsheet = service.spreadsheets().get(spreadsheetId=CRM_SHEET_ID).execute()
    tabs = [s["properties"]["title"] for s in spreadsheet["sheets"]]
    missing = [t for t in EXPECTED_TABS if t not in tabs]
    if missing:
        raise SystemExit(f"Missing tabs: {missing}")

    for tab, expected in EXPECTED_HEADERS.items():
        rows = read_sheet_rows(service, tab)
        values = rows[0] if rows else []
        if values[: len(expected)] != expected:
            raise SystemExit(f"Header mismatch in {tab}: {values}")

    print(json.dumps({"status": "ok", "spreadsheetId": CRM_SHEET_ID, "tabs": tabs, "checked_headers": sorted(EXPECTED_HEADERS)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
