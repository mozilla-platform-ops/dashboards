# yardstick

Backup of RelSRE-owned dashboards, folders, and alert rules from
`yardstick.mozilla.org` (Mozilla's self-hosted Grafana). Pulled via
[`gcx`](https://github.com/grafana/gcx) and the Grafana provisioning API
through Mozilla's `mzcld` IAP proxy.

## Layout

```
yardstick/
├── Makefile               # backup / push / validate / diff / discover-uids
├── scripts/
│   └── pull_alerts.py     # alert rules via /api/v1/provisioning (gcx alert yaml carries live state)
├── resources/             # `gcx resources pull` target — one yaml per resource
│   ├── dashboards.v0alpha1.dashboard.grafana.app/<UID>.yaml
│   ├── dashboards.v1beta1.dashboard.grafana.app/<UID>.yaml   # newer-API dashboards land here
│   └── folders.v1beta1.folder.grafana.app/<UID>.yaml
└── alerts/                # one cleaned JSON per RelSRE alert rule
    └── <title-slug>.json
```

Folder hierarchy on Yardstick is encoded inside each yaml's
`metadata.annotations["grafana.app/folder"]` (pointing at the parent UID),
not in the on-disk directory layout. `gcx resources pull` and
`gcx resources push` round-trip the same shape, so the flat-by-kind tree
is what gcx wants.

Scope is hardcoded in the Makefile (`FOLDER_UIDS`, `DASHBOARD_UIDS`) and
mirrored in `pull_alerts.py` (`RELSRE_FOLDER_UIDS`). Keep them in sync.
`make discover-uids` lists current UIDs to help refresh the Makefile when
dashboards are added or removed.

## Prerequisites

See the top-level [`README.md`](../README.md) `gcx` section for the full
install + auth flow. In short:

1. `brew install grafana/grafana/gcx`
2. `go install github.com/mozilla/mozcloud/tools/mzcld@latest`
3. Service-account token in 1Password as `Grafana Yardstick Service Account Token`
4. `gcloud auth login`
5. Start the IAP proxy: `mzcld iap --host yardstick.mozilla.org --proxy --port 3000`
6. `gcx login yardstick --server http://localhost:3000 --token "$(op read 'op://RelOps/Grafana Yardstick Service Account Token/credential')" --yes && gcx config use-context yardstick`

## Workflow

```bash
make help            # list targets

# back up live state into resources/ + alerts/
make backup

# preview drift without writing files
make diff

# push local edits back to Yardstick (dashboards/folders only)
make push

# server-side validation
make validate

# print live UIDs to refresh the Makefile lists
make discover-uids
```

Environment overrides:
- `BASE_URL` — defaults to `http://localhost:3000`
- `TOKEN_REF` — 1Password reference used by `pull_alerts.py` and
  `discover-uids` (defaults to
  `op://RelOps/Grafana Yardstick Service Account Token/credential`)
- `GRAFANA_TOKEN` — if set, scripts use it directly and skip `op read`.
  See *Credential persistence* below.

## Credential persistence

The Yardstick service-account token is stored in 1Password
(`op://RelOps/Grafana Yardstick Service Account Token/credential`).
Two layers cache it during day-to-day work:

1. **gcx caches its token after the first login.** Running
   `gcx login yardstick --server http://localhost:3000 --token "$(op read ...)" --yes`
   writes the token to `~/.config/gcx/config.yaml`. Subsequent
   `gcx ...` commands (including `make backup`, `make push`, etc.)
   reuse that cached token automatically — you do **not** pass
   `--token` again. Re-run `gcx login` only after token rotation or to
   point at a different stack.
2. **Shell env var for the scripts.** `pull_alerts.py` and the
   `discover-uids` curl loop call `op read` by default, which prompts
   1Password each invocation. To suppress that, cache the token once
   per shell:

   ```bash
   export GRAFANA_TOKEN=$(op read 'op://RelOps/Grafana Yardstick Service Account Token/credential')
   ```

   `pull_alerts.py` and `make discover-uids` pick up `GRAFANA_TOKEN`
   first and only fall back to `op read` when it is unset. To avoid
   leaving the token in shell history, prefer
   [`op run`](https://developer.1password.com/docs/cli/reference/commands/run/)
   with an `.env` file (gitignored).

The token in `~/.config/gcx/config.yaml` is stored in plain text — same
caveat as the SRE Confluence guide. Treat that file like any other
credential at rest.

## Editing dashboards

1. `make backup` to sync local state.
2. Edit the relevant yaml under `resources/`.
3. `make validate` (server-side schema check) and `make diff` (preview).
4. `make push` to apply, then `make backup` again to reconcile any
   server-injected fields and commit the result.

## Editing alert rules

`gcx resources push` does not handle alert rules cleanly (the yaml format
is live-state-polluted), so alert edits go through the Grafana UI or
Terraform. `make backup` re-pulls them after the change so the JSON in
`alerts/` matches production.

## Gotchas

- `gcx dashboards search --folder <name>` returns empty against
  Yardstick's nested-folder layout. Use folder UIDs via the underlying
  `/api/search?folderUIDs=<UID>` endpoint (`make discover-uids` does
  this).
- gcx splits dashboards across API versions (`v0alpha1`, `v1beta1`). Both
  directories are tracked; do not delete one assuming it is stale.
- Yardstick is behind Google IAP. Every command that hits
  `http://localhost:3000` requires `mzcld iap` running.
