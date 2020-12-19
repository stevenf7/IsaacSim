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
               # Use package in _build/packages
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

# Nucleus server credentials
export OMNI_USER=ov-test
export OMNI_PASS=ov-test

cd "$SCRIPT_DIR/../../../../tools"
./test.sh --suite pythontests --config $CONFIG $USE_PACKAGE $PARAMS
./test.sh --suite unittests --config $CONFIG $USE_PACKAGE $PARAMS