#!/bin/bash
set -e

#export PM_S3_ID=
#export PM_S3_KEY=

SCRIPT_DIR=$(dirname ${BASH_SOURCE})
source "$SCRIPT_DIR/packman/packman" push -r cloudfront_upload -v -mp $@ || exit $?
