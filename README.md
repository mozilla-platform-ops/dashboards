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

### install

```bash
brew install grafana/grafana/gcx
```

### authenticate against Yardstick

Yardstick at `https://yardstick.mozilla.org` is behind SSO and rejects
service-account tokens directly. Authenticate against the local proxy on
`http://localhost:3000` instead, using the service-account token stored in
1Password as `Grafana Yardstick Service Account Token` (RelOps vault):

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
