#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "${BASH_SOURCE}")"

if [ ! -z "$TEAMCITY_VERSION" ]
then
    package="--from-package"
fi

case $variable in
     release)      
          CONFIG=release
          ;;
     debug)      
          CONFIG=release
          ;;
     --from-package)
          package="--from-package"
          ;; 
     *)
          ;;
esac

if [ "$CONFIG" == "" ]
then
    CONFIG="release"
fi

export OMNI_USER=test
export OMNI_PASS=test
"$SCRIPT_DIR/../../../../tools/test.sh" --suite pythontests --config $CONFIG $package $*