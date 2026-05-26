# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A version-controlled backup of Mozilla RelSRE Grafana dashboards, folders,
and alert rules from `yardstick.mozilla.org`. No build/lint/test pipeline —
changes land as YAML/JSON diffs reviewed in PRs.

## Repo layout

- `yardstick/` — **active** RelSRE backup from Yardstick. All current work
  happens here.
  - `Makefile` — `make backup / push / validate / diff / discover-uids`.
    Scope is hardcoded in `FOLDER_UIDS` and `DASHBOARD_UIDS`; mirror
    changes into `scripts/pull_alerts.py:RELSRE_FOLDER_UIDS`.
  - `scripts/pull_alerts.py` — alert-rule backup via the Grafana
    provisioning API (gcx's alert yaml carries live evaluation state and
    is not usable for committing).
  - `resources/` — `gcx resources pull` / `push` target. Flat by kind:
    `dashboards.v0alpha1.dashboard.grafana.app/<UID>.yaml`,
    `dashboards.v1beta1.dashboard.grafana.app/<UID>.yaml`,
    `folders.v1beta1.folder.grafana.app/<UID>.yaml`. Folder hierarchy
    lives in `metadata.annotations["grafana.app/folder"]`, not on disk.
  - `alerts/` — one stripped JSON per RelSRE alert rule
    (`<title-slug>.json`).
- `earthangel/` — **historical** backups of the old Influx-based hosted
  Grafana (wizzy and an early gdg attempt). Read-only reference.

## Daily workflow

1. Start the IAP proxy in another terminal:
   `mzcld iap --host yardstick.mozilla.org --proxy --port 3000`.
2. `cd yardstick && make backup` (or `make diff` to preview without
   writing). gcx talks to `http://localhost:3000`; the proxy injects the
   Google IAP token automatically.
3. Edit YAML under `resources/`, `make validate` then `make push`, then
   `make backup` once more to capture any server-injected fields.

## Hard rules for backup/update PRs

- Never delete dashboards as part of a routine backup. If a dashboard
  disappears upstream, confirm intent before committing the deletion.
- Alert rules are pushed via the Grafana UI or Terraform, not
  `gcx resources push` (gcx alert yaml is live-state-polluted).
- Strip server-churn fields (`id`, `updated`, `version`) from alert JSON —
  `pull_alerts.py` already does this; don't reintroduce them.
- `RelSRE Sandboxes` (folder UID `dedlat92kts74e`) is intentionally not in
  `FOLDER_UIDS` / `RELSRE_FOLDER_UIDS` — keep it that way.

## Yardstick-specific gotchas

- `https://yardstick.mozilla.org` is behind Google IAP. Every command that
  hits `http://localhost:3000` requires `mzcld iap` running locally.
- `gcx dashboards search --folder <name>` returns empty against
  Yardstick's nested-folder layout. Use `/api/search?folderUIDs=<UID>`
  (which is what `make discover-uids` does).
- gcx splits dashboards across multiple API versions (`v0alpha1`,
  `v1beta1`). Both directories under `yardstick/resources/` are real;
  don't delete one assuming it is stale.
- Yardstick rotates session tokens aggressively; service-account tokens
  via the IAP proxy are the supported path, not browser cookies.
