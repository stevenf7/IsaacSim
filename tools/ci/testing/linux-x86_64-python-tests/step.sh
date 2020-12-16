#!/usr/bin/env bash

set -e

PARAMS=""
SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

while (( "$#" )); do
     case $1 in
          release)      
               CONFIG=release
               shift
               ;;
          debug)      
               CONFIG=debug
               shift
               ;;
          package)
               USE_PACKAGE="--from-package"
               shift
               ;; 
          *)
               PARAMS="$PARAMS $1"
               shift
               ;;
     esac
done

if [ "$CONFIG" == "" ]
then
    CONFIG="release"
fi

export OMNI_USER=test
export OMNI_PASS=test

cd "$SCRIPT_DIR/../../../../tools"
./test.sh --suite pythontests --config $CONFIG $USE_PACKAGE $PARAMS