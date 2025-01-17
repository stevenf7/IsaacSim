#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../repo.sh" extension_docs --error-as-warn $@
"$SCRIPT_DIR/../repo.sh" docs -c release --warn-as-error=0 $@
