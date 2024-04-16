#!/bin/bash

export PM_MODULE_DIR_EXT="$(dirname ${BASH_SOURCE})/../common"

source "$(dirname ${BASH_SOURCE})/packman.sh" $*

unset PM_MODULE_DIR_EXT

