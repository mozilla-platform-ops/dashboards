# Notes

This backup was generated with https://github.com/esnet/gdg as wizzy isn't working any longer.

https://github.com/esnet/gdg

## usage

### first setup

```bash
# view help
./run_gdg.sh help

# replace config/importer.yml with the 1Password file
# and rerun.

# should now not just warn, but show help
./run_gdg.sh help
```

### backing up

```bash
# backup dashboards
./run_gdg.sh backup dashboards -t relsre-backup

```

### RelSRE folder exports

The RelSRE folder in Yardstick has nested subfolders. Each one maps to a tracked
directory under `dashboards/`:

| Yardstick folder | Tracked dir |
|---|---|
| `RelSRE` (root) | `dashboards/relsre/` |
| `RelSRE/FXCI Cloud Workers/Azure` | `dashboards/fxci-cloud-workers/azure/` |
| `RelSRE/FXCI Cloud Workers/GCP` | `dashboards/fxci-cloud-workers/gcp/` |
| `RelSRE/FXCI Hardware Workers/Linux` | `dashboards/fxci-hardware-workers/linux/` |
| `RelSRE/FXCI Hardware Workers/Mac` | `dashboards/fxci-hardware-workers/mac/` |
| `RelSRE/FXCI Hardware Workers/Windows` | `dashboards/fxci-hardware-workers/windows/` |
| `RelSRE/RelSRE Development` | `dashboards/relsre-development/` |

`RelSRE/RelSRE Sandboxes` is intentionally not tracked (personal/test dashboards).

`yardstick/manual/` is kept as historical manual exports.

#### Preferred: GDG (when working)

After replacing `config/importer.yml` with the 1Password config, GDG can
download the RelSRE folder tree:

```bash
./run_gdg.sh backup dash download -f RelSRE
```

GDG writes dashboard JSON under the configured output path by Grafana folder.
Copy the downloaded JSON into the tracked directories above before committing.

Do not run `clear` or delete dashboards as part of a backup/update PR.

#### Fallback: manual via Grafana API

If GDG is not set up locally (no Docker, missing token, etc.), export browser
cookies for `yardstick.mozilla.org` to a Netscape-format cookie file and pull
dashboards directly:

```bash
# list dashboards in a folder
curl -s -b ~/Downloads/cookies.Mozilla.yardstick.txt \
  "https://yardstick.mozilla.org/api/search?folderUIDs=<FOLDER_UID>&type=dash-db&limit=500"

# fetch a single dashboard and strip the meta wrapper
curl -s -b ~/Downloads/cookies.Mozilla.yardstick.txt \
  "https://yardstick.mozilla.org/api/dashboards/uid/<DASH_UID>" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      json.dump(d['dashboard'], sys.stdout, indent=2, sort_keys=True)" \
  > dashboards/<dir>/<slug>.json
```

Yardstick rotates the session token aggressively; if you see
`session.token.rotate`, re-export cookies before continuing.

### misc

```bash
# using another config file
./run_gdg.sh -c config/importer.yml.blah help
```
