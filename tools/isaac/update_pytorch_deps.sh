#!/bin/bash

# Script to update PyTorch dependencies in pip_ml.toml

# Check for required arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <python_version> <pytorch_install_command>"
    echo "Example: $0 3.11 \"pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128\""
    exit 1
fi

PYTHON_VERSION=$1
PYTORCH_INSTALL_CMD=$2
TOML_FILE="deps/pip_ml.toml"

# Check if TOML file exists
if [ ! -f "$TOML_FILE" ]; then
    echo "Error: $TOML_FILE not found."
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

# Run the Python script to update the TOML file
echo "Updating $TOML_FILE..."
python tools/isaac/update_toml.py "$TEMP_DIR/requirements.txt" "$TOML_FILE"

# Deactivate the virtual environment
deactivate

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_DIR"

echo "Done! Updated PyTorch dependencies in $TOML_FILE" 