#!/bin/bash

set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# Test apt update
apt update

# Test pip install
cd "$SCRIPT_DIR/.."


./jupyter_notebook.sh test standalone_examples/testing/notebooks/basic_notebook.ipynb
./jupyter_notebook.sh test standalone_examples/testing/notebooks/test_ogn_notebook.ipynb
./jupyter_notebook.sh test standalone_examples/testing/notebooks/test_syntheticdata_notebook.ipynb