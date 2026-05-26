# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A version-controlled backup of Mozilla RelSRE Grafana dashboards,
folders, and alert rules from `yardstick.mozilla.org`. No build / lint /
test pipeline — changes land as JSON diffs reviewed in PRs.

## Repo layout

- `yardstick/` — **active** RelSRE backup. All current work happens here.
  - `Makefile` — `make login / backup / diff / discover-uids`.
  - `scripts/backup.py` — pulls dashboards via `/api/dashboards/uid/`
    and alert rules via `/api/v1/provisioning/alert-rules`. Scope is
    hardcoded in `FOLDERS` (UID → on-disk slug); update it when folders
    are added or renamed in Yardstick. `make discover-uids` prints the
    live list to help.
  - `dashboards/<folder-slug>/<title-slug>.json` — one dashboard per
    file, in a human folder hierarchy mirroring the RelSRE tree.
  - `alerts/<folder-slug>/<title-slug>.json` — same layout for alert
    rules.
- `earthangel/` — **historical** backups of the old Influx-based hosted
  Grafana (wizzy and an early gdg attempt). Read-only reference.

`gcx` is **not** used for backups. Its native `gcx resources pull/push`
layout is a Kubernetes-style GVK tree with UID filenames, split across
`v0alpha1`/`v1beta1` API versions — unreviewable in PRs. `gcx` stays
installed for ad-hoc CLI work (`gcx dashboards search`, `gcx metrics
query`) and the bundled agent skills, but the backup loop is the small
Python script.

## Daily workflow

1. Start the IAP proxy in another terminal:
   `mzcld iap --host yardstick.mozilla.org --proxy --port 3000`.
   (`https://yardstick.mozilla.org` is behind Google IAP and rejects
   service-account tokens directly.)
2. `cd yardstick && make backup` (or `make diff` to preview without
   writing). The script reads the token from `GRAFANA_TOKEN` if
   exported, otherwise via `op read $TOKEN_REF`.
3. Edit dashboards in the Grafana UI (or alert rules via UI/Terraform);
   `make backup` again to capture the change, then commit the diff.

There is no `make push`. Round-trip GitOps was tried and reverted —
the on-disk layout it required was too noisy for review.

## Hard rules for backup/update PRs

- Never delete dashboards as part of a routine backup. If a dashboard
  disappears upstream, confirm intent before committing the deletion.
- Strip server-churn fields (`id`, `version` for dashboards; `id`,
  `updated`, `version` for alerts) — `scripts/backup.py` already does
  this; don't reintroduce them.
- `RelSRE Sandboxes` (folder UID `dedlat92kts74e`) is intentionally
  absent from `FOLDERS` — keep it that way.
- Intermediate folders `FXCI Cloud Workers` (`efmrv608qkr28f`) and
  `FXCI Hardware Workers` (`cffmfl1sfr1moe`) are listed in `FOLDERS`
  with `None` because they contain only subfolders today. Change to a
  slug if dashboards land in them directly.

## Yardstick-specific gotchas

- `gcx dashboards search --folder <name>` returns empty against
  Yardstick's nested-folder layout. Use `/api/search?folderUIDs=<UID>`
  (which is what `make discover-uids` does).
- Yardstick rotates session tokens aggressively; service-account tokens
  via the IAP proxy are the supported path, not browser cookies.
- The previous gcx-native `yardstick/resources/` tree was removed when
  we switched back to the human layout. Don't reintroduce it without
  re-discussing the tradeoff.
