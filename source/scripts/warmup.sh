#!/bin/bash
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Use half of available CPU cores for the warmup not to take all the resources from user's PC during installation
TASKING_THREAD_CNT=$(nproc --all)
TASKING_THREAD_CNT=$(($TASKING_THREAD_CNT/2))

set +e # Workaround post-install script failure
# Warm up shader cache for Python app
"$SCRIPT_DIR/python.sh" "$SCRIPT_DIR/standalone_examples/api/isaacsim.simulation_app/hello_world.py"
echo "Python app shader cache is warmed up."

# Warm up shader cache
"$SCRIPT_DIR/kit/kit" "$SCRIPT_DIR/apps/isaacsim.exp.base.kit" \
    --no-window \
    --/persistent/renderer/startupMessageDisplayed=true \
    --ext-folder "$SCRIPT_DIR/exts" \
    --ext-folder "$SCRIPT_DIR/apps" \
    --/app/settings/persistent=0 \
    --/app/settings/loadUserConfig=0 \
    --/structuredLog/enable=0 \
    --/app/hangDetector/enabled=0 \
    --/crashreporter/skipOldDumpUpload=1 \
    --/app/content/emptyStageOnStart=1 \
    --/rtx/materialDb/syncLoads=1 \
    --/omni.kit.plugin/syncUsdLoads=1 \
    --/rtx/hydra/materialSyncLoads=1 \
    --/app/asyncRendering=0 \
    --/app/quitAfter=1000 \
    --/app/fastShutdown=1 \
    --/app/file/ignoreUnsavedOnExit=1 \
    --/app/warmupMode=1 \
    --/exts/omni.kit.registry.nucleus/registries/0/name=0 \
    --/plugins/carb.tasking.plugin/threadCount=$TASKING_THREAD_CNT
echo "Shader cache is warmed up."
set -e
