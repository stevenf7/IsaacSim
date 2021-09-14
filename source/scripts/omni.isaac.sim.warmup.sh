#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
TASKING_THREAD_CNT=$(nproc --all)
TASKING_THREAD_CNT=$(($TASKING_THREAD_CNT/2))
exec "$SCRIPT_DIR/kit/kit" "$SCRIPT_DIR/apps/omni.isaac.sim.warmup.kit" --no-window --ext-folder "$SCRIPT_DIR/exts" --ext-folder "$SCRIPT_DIR/apps" --/plugins/carb.tasking.plugin/threadCount=$TASKING_THREAD_CNT