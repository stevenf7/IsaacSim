#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Remove repo log file if it exists
rm -f "$SCRIPT_DIR/../_repo/repo.log"
"$SCRIPT_DIR/../repo.sh" generate_doxygen_input
"$SCRIPT_DIR/../repo.sh" extension_toc --error-as-warn $@
"$SCRIPT_DIR/../repo.sh" extension_docs --error-as-warn $@
"$SCRIPT_DIR/../repo.sh" docs -c release --warn-as-error=0 $@
"$SCRIPT_DIR/../repo.sh" generate_examples_list $@
