#!/bin/bash

QUERY_TIME=30
KILL_TIME=1800

KILL_TIMER=0

read STATUS < /tmp/replicator_status.txt
# echo "status" $STATUS

while [[ $STATUS != "FINISHED" ]]
do
    if [ $KILL_TIMER -gt $KILL_TIME ]
    then
        # echo "KILL"
        ps aux | grep generator.py | awk '{print $2}' | xargs kill -9
        KILL_TIMER=0
    fi

    read STATUS < /tmp/replicator_status.txt
    # echo "status" $STATUS "kill_timer" $KILL_TIMER

    sleep $QUERY_TIME

    KILL_TIMER=$(($KILL_TIMER + $QUERY_TIME))
done