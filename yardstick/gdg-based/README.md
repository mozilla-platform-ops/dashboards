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

Use `dashboards/relsre/` as the tracked location for Yardstick RelSRE dashboards.
This mirrors the existing `earthangel/gdg-based/dashboards/relops/` layout while
keeping the older `yardstick/manual/` files as historical manual exports.

After replacing `config/importer.yml` with the 1Password config, use GDG to
download the RelSRE folder:

```bash
./run_gdg.sh backup dash download -f RelSRE
```

GDG writes dashboard JSON under the configured output path by Grafana folder.
Keep the RelSRE exports in `dashboards/relsre/` when committing them to this
repo. If the local GDG output path differs, copy the downloaded RelSRE dashboard
JSON into `dashboards/relsre/` before committing.

Do not run `clear` or delete dashboards as part of a backup/update PR.

### misc

```bash
# using another config file
./run_gdg.sh -c config/importer.yml.blah help
```
