#!/usr/bin/env python3
"""Shared SponsorOS Google helpers with strict isolation guard."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REQUIRED_HERMES_HOME = "/Users/clawd/.hermes-sponsoros"
CRM_SHEET_ID = "10IJPrZBE3JJoh7ePeslBeAY10yLxDT0WFaPUHoqPFwY"


class SponsorOSEnvironmentError(RuntimeError):
    """Raised when SponsorOS env guard fails."""


def require_sponsoros_env() -> Path:
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home != REQUIRED_HERMES_HOME:
        raise SponsorOSEnvironmentError(
            f"Wrong HERMES_HOME. Expected {REQUIRED_HERMES_HOME}."
        )
    return Path(REQUIRED_HERMES_HOME)


def _load_authorized_creds(scopes: Optional[Iterable[str]] = None) -> Credentials:
    home = require_sponsoros_env()
    token_path = home / "google_token.json"
    if not token_path.exists():
        raise SponsorOSEnvironmentError(f"Missing token file: {token_path}")

    token_data = json.loads(token_path.read_text(encoding="utf-8"))
    requested_scopes = list(scopes) if scopes else token_data.get("scopes")
    creds = Credentials.from_authorized_user_file(str(token_path), requested_scopes)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def build_sheets_service(scopes: Optional[Iterable[str]] = None):
    creds = _load_authorized_creds(scopes)
    return build("sheets", "v4", credentials=creds)


def build_gmail_service(scopes: Optional[Iterable[str]] = None):
    creds = _load_authorized_creds(scopes)
    return build("gmail", "v1", credentials=creds)


def read_sheet_rows(service, tab_name: str):
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=CRM_SHEET_ID, range=f"{tab_name}!A:ZZ")
        .execute()
    )
    return result.get("values", [])


def rows_to_dicts(rows: list[list[str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    header = rows[0]
    out: list[dict[str, str]] = []
    for row in rows[1:]:
        item = {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
        out.append(item)
    return out
