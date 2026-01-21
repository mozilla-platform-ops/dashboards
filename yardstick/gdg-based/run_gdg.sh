#!/usr/bin/env bash

set -e
# debug
# set -x

CONFIG_FILE="config/importer.yml"

# show getopts detected args
echo "getopts detected args: $@"

# Check if '-c config_file' is passed as argument
while getopts ":c:" opt; do
    case ${opt} in
        c )
            CONFIG_FILE=$OPTARG
            # CONFIG_FILE_ARG has '-c config_file' format
            CONFIG_FILE_ARG="-c $CONFIG_FILE"
            ;;
        \? )
            echo "Usage: run_gdg.sh [-c config_file]"
            exit 1
            ;;
    esac
done
shift $((OPTIND-1))
OTHERARGS=$@

echo "getopts detected args: $@"

# Check if config file exists and contains replacement tag
if [ -f "$CONFIG_FILE" ]; then
    if grep -q "AUTOMATION_TAG_REPLACE_README_CONFIG" "$CONFIG_FILE"; then
        cat "$CONFIG_FILE"
        exit 1
    fi
fi

set -x

docker run --platform linux/amd64 -it --rm \
    -v "$(pwd)/config:/app/config" \
    -v "$(pwd)/exports:/app/exports" \
    ghcr.io/esnet/gdg:latest $CONFIG_FILE_ARG $@
