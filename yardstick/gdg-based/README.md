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

### misc

```bash
# using another config file
./run_gdg.sh -c config/importer.yml.blah help
```
