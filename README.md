# monitoring dashboards
backup of grafana dashboards

## structure

```
earthangel/ - our original hosted-grafana dashboards, influx based
yardstick/ - our newer self-hosted grafana dashboards, prometheus based
```

## tools

We previously used the now-deprecated Wizzy (https://github.com/grafana-wizzy/wizzy).

We're using GDG (https://github.com/esnet/gdg) now. See
[`yardstick/gdg-based/README.md`](yardstick/gdg-based/README.md) for the GDG
workflow against Yardstick.

## gcx

[`gcx`](https://github.com/grafana/gcx) is the Grafana CLI. It's useful for
ad-hoc inspection of Yardstick dashboards, alert rules, and datasources
without exporting browser cookies or running Docker.

Mozilla's full guide is in the SRE Confluence:
[How to: Use Grafana with Claude Code, Grafana MCP, and Grafana gcx](https://mozilla-hub.atlassian.net/wiki/spaces/SRE/pages/2641985695/How+to+Use+Grafana+with+Claude+Code+Grafana+MCP+and+Grafana+gcx).

### prerequisites

1. A Grafana service-account token for Yardstick, stored in 1Password.
   Request one via the [SRE Infrastructure form](https://mozilla-hub.atlassian.net/jira/software/c/projects/SREIN/form/1344)
   (Editor role, name like `firstname-lastname-claude`). Detailed steps:
   [How to: Create and manage Yardstick accounts and access](https://mozilla-hub.atlassian.net/wiki/spaces/SRE/pages/1695350962).
2. `gcloud` authenticated (`gcloud auth login`) — `mzcld` uses it to mint
   Google IAP tokens.
3. The 1Password CLI (`op`).

### install gcx

```bash
brew install grafana/grafana/gcx
```

### install mzcld (IAP proxy for Yardstick)

`https://yardstick.mozilla.org` is protected by Google IAP, so `gcx` and the
Grafana MCP cannot talk to it directly. [`mzcld`](https://github.com/mozilla/mozcloud/tree/main/tools/mzcld)
runs a local proxy on `http://localhost:3000` that injects and refreshes the
IAP token automatically.

```bash
go install github.com/mozilla/mozcloud/tools/mzcld@latest
```

### start the proxy

Leave this running in a separate terminal while you use `gcx`:

```bash
mzcld iap --host yardstick.mozilla.org --proxy --port 3000
```

Verify:

```bash
curl -s http://localhost:3000/api/health | jq .
# { "database": "ok", "version": "12.x.x", ... }
```

### authenticate gcx against Yardstick

With the proxy running, authenticate `gcx` against `http://localhost:3000`
using the service-account token stored in 1Password (default item name:
`Grafana Yardstick Service Account Token` in the RelOps vault — adjust the
`op://` path to match your own item):

```bash
gcx login yardstick \
  --server http://localhost:3000 \
  --token "$(op read 'op://RelOps/Grafana Yardstick Service Account Token/credential')" \
  --yes
gcx config use-context yardstick
gcx config check        # should report ✔ Connectivity and the Grafana version
```

### interact with dashboards

```bash
# list all dashboards in the current context
gcx dashboards list

# search by title
gcx dashboards search "workers"

# fetch one dashboard as JSON (UID from list/search output)
gcx dashboards get <UID> -o json
```

`gcx dashboards search --folder <name>` does **not** work against Yardstick's
nested-folder layout — it returns an empty list. Filter by folder UID through
the underlying API instead, e.g.:

```bash
TOKEN=$(op read 'op://RelOps/Grafana Yardstick Service Account Token/credential')
curl -sS -H "Authorization: Bearer $TOKEN" \
  'http://localhost:3000/api/folders' | jq '.[] | select(.title=="RelSRE")'
curl -sS -H "Authorization: Bearer $TOKEN" \
  'http://localhost:3000/api/search?folderUIDs=<FOLDER_UID>&type=dash-db&limit=500' \
  | jq -r '.[] | "\(.title)\t\(.uid)"'
```

To enumerate the full RelSRE subfolder tree, walk
`/api/folders?parentUid=<UID>` for each level.

### other resources

`gcx` covers alert rules, datasources, SLOs, and more. See `gcx --help` and
the agent skills bundled with the CLI:

```bash
gcx agent skills list
```
