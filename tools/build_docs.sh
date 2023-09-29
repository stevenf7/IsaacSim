#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
"$SCRIPT_DIR/../repo.sh" omnigraph_docs $@ 
"$SCRIPT_DIR/../repo.sh" docs -c release --warn-as-error=0 $@
