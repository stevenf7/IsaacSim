#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Use half of available CPU cores for the warmup not to take all the resources from user's PC during installation
TASKING_THREAD_CNT=$(nproc --all)
TASKING_THREAD_CNT=$(($TASKING_THREAD_CNT/2))
exec "$SCRIPT_DIR/kit/kit" "$SCRIPT_DIR/apps/omni.isaac.sim.kit" \
    --no-window \
    --ext-folder "$SCRIPT_DIR/exts" \
    --ext-folder "$SCRIPT_DIR/apps" \
    --/app/settings/persistent=0 \
    --/app/settings/loadUserConfig=0 \
    --/structuredLog/enable=0 \
    --/app/hangDetector/enabled=0 \
    --/app/content/emptyStageOnStart=1 \
    --/rtx/materialDb/syncLoads=1 \
    --/omni.kit.plugin/syncUsdLoads=1 \
    --/rtx/hydra/materialSyncLoads=1 \
    --/app/asyncRendering=0 \
    --/app/quitAfter=10 \
    --/app/fastShutdown=true \
    --/exts/omni.kit.registry.nucleus/registries/0/name=0 \
    --/plugins/carb.tasking.plugin/threadCount=$TASKING_THREAD_CNT \
    "$@"