#!/usr/bin/env python3
"""Assert there are no send/draft/modify email workflows in code paths."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [ROOT / "scripts", ROOT / "public"]
ALLOWED_SUFFIXES = {".py", ".html", ".js", ".ts", ".tsx", ".jsx", ".json"}
SKIP_SCRIPT_NAMES = {"verify_no_send_paths.py", "verify_approval_ui.py"}

# These patterns indicate prohibited send/draft operations when used with Gmail API.
BANNED_PATTERNS = [
    r"\.messages\(\)\.send\(",
    r"\.drafts\(\)\.create\(",
    r"\.drafts\(\)\.send\(",
    r"gmail\.modify",
    r"users\(\)\.messages\(\)\.modify\(",
    r"mailto:",
    r"\bsmtp\b",
    r"fetch\(['\"]https?://",
]


def main() -> int:
    offenders = []
    for base in SCAN_DIRS:
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
                continue
            if path.parent.name == "scripts" and path.name in SKIP_SCRIPT_NAMES:
                continue
            text = path.read_text(encoding="utf-8")
            for pat in BANNED_PATTERNS:
                if re.search(pat, text, flags=re.IGNORECASE):
                    offenders.append((str(path), pat))

    if offenders:
        lines = [f"{p} matched {pat}" for p, pat in offenders]
        raise SystemExit("Prohibited Gmail send/modify path found:\n" + "\n".join(lines))

    print("no send/modify gmail paths found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
