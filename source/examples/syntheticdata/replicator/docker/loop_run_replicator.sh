#!/bin/bash

CMD="./python.sh python_samples/syntheticdata/replicator/generator.py $*"

# Loop command until success
# echo "LAUNCH"
$CMD
while [ $? -ne 0 ]; do
       sleep 10
       # echo "LAUNCH"
       $CMD
done       

status="FINISHED"
echo $status > /tmp/replicator_status.txt
