#!/usr/bin/env python3
"""Fail-fast isolation guard for SponsorOS local workspace."""

import os
import sys

REQUIRED_HERMES_HOME = "/Users/clawd/.hermes-sponsoros"


def main() -> int:
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home != REQUIRED_HERMES_HOME:
        print("ERROR: SponsorOS isolation guard failed.", file=sys.stderr)
        print(
            f"Set HERMES_HOME={REQUIRED_HERMES_HOME} before running SponsorOS workflows.",
            file=sys.stderr,
        )
        print("No credentialed actions are allowed in this mode.", file=sys.stderr)
        return 1

    print("SponsorOS isolation guard passed.")
    print(f"HERMES_HOME={hermes_home}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
