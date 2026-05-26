# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A version-controlled backup of Mozilla RelSRE Grafana dashboards (and the alert rules that live alongside them). No build, lint, or test pipeline — changes land as JSON diffs reviewed in PRs.

## Repo layout

- `yardstick/` — **active** backups for the current self-hosted Prometheus-based Grafana (https://yardstick.mozilla.org). Touch this tree for any current work.
  - `gdg-based/dashboards/` — tracked dashboard JSON, organized to mirror the RelSRE folder tree in Yardstick. See the mapping table in `yardstick/gdg-based/README.md`.
  - `gdg-based/alerts/` — alert-rule JSON mirroring the same folder layout. Alert rules live in the same Grafana folder as the dashboards they monitor (per the RelSRE wiki).
  - `gdg-based/config/importer.yml` — placeholder; replace with the real config from 1Password before running GDG.
  - `gdg-based/run_gdg.sh` — runs the `ghcr.io/esnet/gdg` Docker image with `config/` and `exports/` mounted in.
  - `manual/` — historical one-off exports; do not add new files here.
- `earthangel/` — **historical** backups of the previous Influx-based hosted Grafana (wizzy and an early gdg attempt). Read-only reference; do not add new dashboards here.

## Backing up dashboards and alerts

Three working methods, in preference order:

1. **GDG (preferred when set up):** drop the 1Password `importer.yml` into `yardstick/gdg-based/config/`, then `./run_gdg.sh backup dash download -f RelSRE`. Copy GDG's output into the tracked directories above before committing.
2. **gcx via local Yardstick proxy:** see the top-level `README.md` `gcx` section. Auth uses the 1Password item `op://RelOps/Grafana Yardstick Service Account Token` against `http://localhost:3000`. Direct `https://yardstick.mozilla.org` is behind SSO and rejects service-account tokens.
3. **Raw curl fallback:** Netscape-format cookies from `yardstick.mozilla.org` + `/api/search?folderUIDs=<UID>` and `/api/dashboards/uid/<UID>`. See `yardstick/gdg-based/README.md` for exact commands.

## Hard rules for backup/update PRs

- Never run `clear` or delete dashboards as part of a backup/update PR — only add or modify the JSON for what changed.
- Strip server-churn fields (`id`, `updated`, `version`) from alert-rule JSON before committing so diffs stay clean.
- `RelSRE/RelSRE Sandboxes` is intentionally untracked (personal/test dashboards). Do not start tracking it.

## Yardstick-specific gotchas

- `gcx dashboards search --folder <name>` returns empty against Yardstick's nested-folder layout. Use `/api/search?folderUIDs=<UID>` (or the gcx equivalent against a specific UID) for folder filtering.
- Yardstick rotates session tokens aggressively; if a manual curl pull surfaces `session.token.rotate`, re-export cookies before continuing.
