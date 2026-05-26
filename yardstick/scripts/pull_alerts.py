#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Pull RelSRE alert rules into yardstick/alerts/, one cleaned JSON per rule.

gcx's alert rule yaml carries live evaluation state (lastEvaluation,
active alerts, timestamps), so backups via `gcx resources pull alertrules`
churn on every run. We hit the provisioning API directly, strip the
server-churn fields, and write one stable file per rule.

Scope mirrors the FOLDER_UIDS list in the Makefile; keep them in sync.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")
TOKEN_REF = os.environ.get(
    "TOKEN_REF",
    "op://RelOps/Grafana Yardstick Service Account Token/credential",
)
STRIP_FIELDS = ("id", "updated", "version")
RELSRE_FOLDER_UIDS = frozenset({
    "edtgaia1z6waoe",  # RelSRE (root)
    "efmrv608qkr28f",  # FXCI Cloud Workers
    "bfmrv6ezxze9sa",  # FXCI Cloud Workers / Azure
    "ffmrv6e11wge8e",  # FXCI Cloud Workers / GCP
    "cffmfl1sfr1moe",  # FXCI Hardware Workers
    "afm3plxpfbhfkb",  # FXCI Hardware Workers / Linux
    "cfm3q22tcfpq8a",  # FXCI Hardware Workers / Mac
    "bfib9xp9idu68b",  # FXCI Hardware Workers / Windows
    "cedp4g145xuyod",  # RelSRE Development
})

ALERTS_DIR = Path(__file__).resolve().parent.parent / "alerts"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-")) or "untitled"


def fetch_token() -> str:
    """Return the Yardstick service-account token.

    Prefers `GRAFANA_TOKEN` (set once per shell with
    `export GRAFANA_TOKEN=$(op read ...)`) so we don't shell out to
    1Password on every backup. Falls back to `op read $TOKEN_REF`.
    """
    cached = os.environ.get("GRAFANA_TOKEN")
    if cached:
        return cached.strip()
    return subprocess.check_output(["op", "read", TOKEN_REF], text=True).strip()


def main() -> int:
    token = fetch_token()
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/provisioning/alert-rules",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        rules = json.load(resp)
    if not isinstance(rules, list):
        raise RuntimeError(
            f"/api/v1/provisioning/alert-rules returned {type(rules).__name__}, expected list"
        )

    staging = ALERTS_DIR.with_suffix(".new")
    backup = ALERTS_DIR.with_suffix(".old")
    for tmp in (staging, backup):
        if tmp.exists():
            shutil.rmtree(tmp)
    staging.mkdir()

    used: set[str] = set()
    written = 0
    for rule in rules:
        if rule.get("folderUID") not in RELSRE_FOLDER_UIDS:
            continue
        for field in STRIP_FIELDS:
            rule.pop(field, None)
        slug = slugify(rule.get("title") or rule.get("uid", "unnamed"))
        if slug in used:
            slug = f"{slug}-{rule.get('uid', '')}"
        used.add(slug)
        (staging / f"{slug}.json").write_text(
            json.dumps(rule, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written += 1

    if ALERTS_DIR.exists():
        ALERTS_DIR.rename(backup)
    staging.rename(ALERTS_DIR)
    if backup.exists():
        shutil.rmtree(backup)

    print(f"wrote {written} alert rules to {ALERTS_DIR}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
