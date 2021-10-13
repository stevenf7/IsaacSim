#!/bin/bash

# Save cmd line parameters
while [ $# -gt 0 ]; do
   if [[ $1 == *"--"* ]]; then
        v="${1/--/}"
        declare $v="$2"
   fi

  shift
done

ARGS="--input $input --output $output"

[[ ! -z "${assets_dir}" ]] && ARGS="${ARGS} --assets-dir $assets_dir"
[[ ! -z "${num_samples}" ]] && ARGS="${ARGS} --num-samples $num_samples"
[[ ! -z "${visualize_models}" ]] && ARGS="${ARGS} --visualize-models"

REPLICATOR_ARGS="${ARGS} --no-overwrite --headless --allow-root --no-window"

LOOP_RUN_REPLICATOR="./loop_run_replicator.sh $REPLICATOR_ARGS"
LOOP_KILL_REPLICATOR="./loop_kill_replicator.sh"

rm /tmp/replicator_status.txt
touch /tmp/replicator_status.txt

$LOOP_RUN_REPLICATOR & $LOOP_KILL_REPLICATOR