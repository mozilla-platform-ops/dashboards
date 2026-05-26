# yardstick

Backup of RelSRE-owned dashboards, folders, and alert rules from
`yardstick.mozilla.org`. Pulled via the Grafana REST API through
Mozilla's `mzcld` IAP proxy and committed as JSON in a human-readable
folder tree.

## Layout

```
yardstick/
├── Makefile               # login / backup / diff / discover-uids
├── scripts/
│   └── backup.py          # pulls dashboards + alerts into the human tree
├── dashboards/
│   ├── relsre/
│   ├── fxci-cloud-workers/{azure,gcp}/
│   ├── fxci-hardware-workers/{linux,mac,windows}/
│   └── relsre-development/
└── alerts/
    ├── relsre/
    ├── fxci-cloud-workers/{azure,gcp}/
    ├── fxci-hardware-workers/{linux,mac,windows}/
    └── relsre-development/
```

Each `<folder-slug>/<title-slug>.json` is a single dashboard or alert
rule, with the server-churn fields (`id`, `version`, plus `updated` for
alerts) stripped so diffs only reflect real edits. The on-disk slug
hierarchy mirrors the Grafana folder tree by hand-curated mapping in
`scripts/backup.py:FOLDERS`. `RelSRE Sandboxes` is intentionally not
tracked.

`gcx` is not the backup tool. Its native `resources pull/push` layout
(Kubernetes GVK directories, UID filenames, split across API versions)
makes PR review unworkable. `gcx` stays installed for ad-hoc commands —
`gcx dashboards search`, `gcx metrics query`, the agent skills — but
not for the round-trip backup loop.

## Prerequisites

See the top-level [`README.md`](../README.md) `gcx` section. In short:

1. `brew install grafana/grafana/gcx`
2. `go install github.com/mozilla/mozcloud/tools/mzcld@latest`
3. Service-account token in 1Password as `Grafana Yardstick Service Account Token`
4. `gcloud auth login`
5. Start the IAP proxy in another terminal:
   `mzcld iap --host yardstick.mozilla.org --proxy --port 3000`

## Workflow

```bash
make help            # list targets

# one-time: log gcx in for ad-hoc queries (not required for backups)
make login

# back up live state into dashboards/ and alerts/
make backup

# preview drift without overwriting files
make diff

# print live UIDs to refresh scripts/backup.py:FOLDERS when folders change
make discover-uids
```

Environment overrides:
- `BASE_URL` — defaults to `http://localhost:3000`
- `TOKEN_REF` — 1Password reference (defaults to
  `op://RelOps/Grafana Yardstick Service Account Token/credential`)
- `CONTEXT` — gcx context name for `make login` (defaults to `yardstick`)
- `GRAFANA_TOKEN` — if set, scripts and `make login` use it directly and
  skip `op read`. See *Credential persistence* below.

## Editing dashboards and alerts

Authoring happens in the Grafana UI (or Terraform for alerts). After
you ship a change:

1. `make backup` to capture the new state.
2. `git diff` to review the JSON changes.
3. Commit and PR.

There is no `make push` — the previous gcx-based round-trip was dropped
because the on-disk layout it required was too noisy for review, and
the team edits dashboards in Grafana anyway.

## Credential persistence

The Yardstick service-account token lives in 1Password
(`op://RelOps/Grafana Yardstick Service Account Token/credential`).
Two layers cache it during day-to-day work:

1. **gcx caches its token after the first login.** `make login` writes
   the token to `~/.config/gcx/config.yaml`; subsequent `gcx`
   commands reuse it. Re-run `make login` after token rotation.
2. **Shell env var for `make backup` / `make discover-uids`.** Without
   `GRAFANA_TOKEN` set, the scripts shell out to `op read` per
   invocation, which prompts 1Password each time. To suppress that:

   ```bash
   export GRAFANA_TOKEN=$(op read 'op://RelOps/Grafana Yardstick Service Account Token/credential')
   ```

   `scripts/backup.py` and `make discover-uids` pick up `GRAFANA_TOKEN`
   first and only fall back to `op read` when it is unset. To keep the
   token out of shell history, prefer
   [`op run`](https://developer.1password.com/docs/cli/reference/commands/run/)
   with a gitignored `.env` file.

The token in `~/.config/gcx/config.yaml` is stored in plain text — same
caveat as the SRE Confluence guide. Treat it like any other secret at
rest.

## Gotchas

- `https://yardstick.mozilla.org` is behind Google IAP; every command
  that hits `http://localhost:3000` requires `mzcld iap` running.
- `gcx dashboards search --folder <name>` returns empty against
  Yardstick's nested folders. `make discover-uids` uses the underlying
  `/api/search?folderUIDs=<UID>` instead.
- Yardstick rotates session tokens aggressively; service-account tokens
  via the IAP proxy are the supported path, not browser cookies.
