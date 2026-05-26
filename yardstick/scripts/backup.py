#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Back up RelSRE Yardstick dashboards and alert rules into a human tree.

Layout:
  yardstick/dashboards/<folder-slug>/<title-slug>.json
  yardstick/alerts/<folder-slug>/<title-slug>.json

Hits the Grafana API directly through the local IAP proxy on
``$BASE_URL``. gcx is not used because its GitOps layout (one dir per
Kubernetes group/version, UID filenames) is unreviewable in PRs.

Writes are staged in sibling ``.new`` directories and only swapped in
once every dashboard and alert has been written, so a fetch or proxy
failure can never leave the working tree half-populated.
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

# Folder UID -> on-disk slug path. ``None`` entries are valid folders we
# traverse but expect to contain no dashboards of their own (intermediate
# parent folders). `RelSRE Sandboxes` is intentionally absent.
FOLDERS: dict[str, str | None] = {
    "edtgaia1z6waoe": "relsre",                            # RelSRE (root)
    "efmrv608qkr28f": None,                                # FXCI Cloud Workers (parent only)
    "bfmrv6ezxze9sa": "fxci-cloud-workers/azure",
    "ffmrv6e11wge8e": "fxci-cloud-workers/gcp",
    "cffmfl1sfr1moe": None,                                # FXCI Hardware Workers (parent only)
    "afm3plxpfbhfkb": "fxci-hardware-workers/linux",
    "cfm3q22tcfpq8a": "fxci-hardware-workers/mac",
    "bfib9xp9idu68b": "fxci-hardware-workers/windows",
    "cedp4g145xuyod": "relsre-development",
}

DASHBOARD_STRIP = ("id", "version")
ALERT_STRIP = ("id", "updated", "version")

YARDSTICK_DIR = Path(__file__).resolve().parent.parent


def fetch_token() -> str:
    cached = os.environ.get("GRAFANA_TOKEN")
    if cached:
        return cached.strip()
    return subprocess.check_output(["op", "read", TOKEN_REF], text=True).strip()


def api_get(path: str, token: str):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-")) or "untitled"


def write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage(name: str) -> tuple[Path, Path]:
    """Return (target_dir, fresh_staging_dir) and clean any stale temp dirs."""
    target = YARDSTICK_DIR / name
    staging = YARDSTICK_DIR / f"{name}.new"
    backup = YARDSTICK_DIR / f"{name}.old"
    for tmp in (staging, backup):
        if tmp.exists():
            shutil.rmtree(tmp)
    staging.mkdir()
    return target, staging


def promote(target: Path, staging: Path) -> None:
    """Atomic swap: rename target→.old, staging→target, then drop .old."""
    backup = YARDSTICK_DIR / f"{target.name}.old"
    if target.exists():
        target.rename(backup)
    staging.rename(target)
    if backup.exists():
        shutil.rmtree(backup)


def unique_slug(used: set[str], title: str, uid: str) -> str:
    slug = slugify(title)
    if slug in used:
        slug = f"{slug}-{uid}"
    used.add(slug)
    return slug


def pull_dashboards(token: str, staging: Path) -> int:
    written = 0
    used_per_dir: dict[str, set[str]] = {}
    for folder_uid, slug in FOLDERS.items():
        if slug is None:
            continue
        rows = api_get(
            f"/api/search?folderUIDs={folder_uid}&type=dash-db&limit=500",
            token,
        )
        for row in rows:
            uid = row["uid"]
            payload = api_get(f"/api/dashboards/uid/{uid}", token)
            dash = payload["dashboard"]
            for field in DASHBOARD_STRIP:
                dash.pop(field, None)
            title = dash.get("title", uid)
            used = used_per_dir.setdefault(slug, set())
            file_slug = unique_slug(used, title, uid)
            write_json(dash, staging / slug / f"{file_slug}.json")
            written += 1
    return written


def pull_alerts(token: str, staging: Path) -> int:
    rules = api_get("/api/v1/provisioning/alert-rules", token)
    if not isinstance(rules, list):
        raise RuntimeError(
            f"/api/v1/provisioning/alert-rules returned {type(rules).__name__}, expected list"
        )
    written = 0
    used_per_dir: dict[str, set[str]] = {}
    for rule in rules:
        slug = FOLDERS.get(rule.get("folderUID"))
        if slug is None:
            continue
        for field in ALERT_STRIP:
            rule.pop(field, None)
        title = rule.get("title") or rule.get("uid", "unnamed")
        used = used_per_dir.setdefault(slug, set())
        file_slug = unique_slug(used, title, rule.get("uid", ""))
        write_json(rule, staging / slug / f"{file_slug}.json")
        written += 1
    return written


def main() -> int:
    token = fetch_token()

    dash_target, dash_staging = stage("dashboards")
    alert_target, alert_staging = stage("alerts")

    dash_count = pull_dashboards(token, dash_staging)
    alert_count = pull_alerts(token, alert_staging)

    promote(dash_target, dash_staging)
    promote(alert_target, alert_staging)

    print(f"wrote {dash_count} dashboards and {alert_count} alert rules", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
