#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Script to update PyTorch dependencies in pip_ml.toml and python_packages.toml

# Check for required arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <python_version> <pytorch_install_command>"
    echo "Example: $0 3.12 \"pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128\""
    exit 1
fi

PYTHON_VERSION=$1
PYTORCH_INSTALL_CMD=$2
PIP_ML_TOML="deps/pip_ml.toml"
PYTHON_PACKAGES_TOML="python_packages.toml"

# Check if TOML files exist
if [ ! -f "$PIP_ML_TOML" ]; then
    echo "Error: $PIP_ML_TOML not found."
    exit 1
fi
if [ ! -f "$PYTHON_PACKAGES_TOML" ]; then
    echo "Error: $PYTHON_PACKAGES_TOML not found."
    exit 1
fi

# Check if the requested Python version is installed
if ! command -v python$PYTHON_VERSION &> /dev/null; then
    echo "Error: Python $PYTHON_VERSION is not installed or not in PATH."
    echo "Please install Python $PYTHON_VERSION or use an available version."
    echo "Available Python versions:"
    ls -1 /usr/bin/python* 2>/dev/null | grep -E 'python[0-9]+(\.[0-9]+)?' || echo "  No Python versions found in /usr/bin"
    which python 2>/dev/null && python --version
    exit 1
fi

# Deactivate any active Python environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating current virtual environment: $VIRTUAL_ENV"
    deactivate
fi

# Deactivate any active conda environment
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "Deactivating current conda environment: $CONDA_DEFAULT_ENV"
    conda deactivate
fi

# Create a temporary directory for the virtual environment
TEMP_DIR=$(mktemp -d)
echo "Creating temporary directory: $TEMP_DIR"

# Create a new virtual environment
echo "Creating new Python $PYTHON_VERSION virtual environment..."
python$PYTHON_VERSION -m venv "$TEMP_DIR/venv"

# Activate the virtual environment
echo "Activating virtual environment..."
source "$TEMP_DIR/venv/bin/activate"

# Update pip
pip install --upgrade pip

# Install PyTorch packages with the provided command
echo "Installing PyTorch packages..."
eval "$PYTORCH_INSTALL_CMD"

# Get installed package versions
echo "Getting installed package versions..."
pip freeze > "$TEMP_DIR/requirements.txt"

# Extract the index URL from the install command (supports both --index-url and --extra-index-url)
INDEX_URL=$(echo "$PYTORCH_INSTALL_CMD" | grep -oP '(?:--index-url|--extra-index-url)\s+\K\S+' | head -1)

# Run the Python script to update the TOML files
echo "Updating $PIP_ML_TOML..."
python tools/isaac/update_toml.py "$TEMP_DIR/requirements.txt" "$PIP_ML_TOML"

echo "Updating $PYTHON_PACKAGES_TOML..."
python tools/isaac/update_toml.py "$TEMP_DIR/requirements.txt" "$PYTHON_PACKAGES_TOML"

if [ -n "$INDEX_URL" ]; then
    echo "Updating extra_args index URL to: $INDEX_URL"
    sed -i 's|extra_args = \["--extra-index-url", "[^"]*"\]|extra_args = ["--extra-index-url", "'"$INDEX_URL"'"]|g' "$PIP_ML_TOML"
else
    echo "Warning: No --index-url or --extra-index-url found in install command, skipping extra_args update."
fi

# Deactivate the virtual environment
deactivate

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Done! Updated PyTorch dependencies in $PIP_ML_TOML and $PYTHON_PACKAGES_TOML"
