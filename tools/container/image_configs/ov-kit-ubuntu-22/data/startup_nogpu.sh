#!/usr/bin/env bash
set -e
set -u

echo 'Running: [...]kit in Non-GPU mode, run startup.sh if a GPU is required.' $@

exec "/opt/nvidia/omniverse/kit-sdk-launcher/kit" \
    "--no-window" \
    $@
