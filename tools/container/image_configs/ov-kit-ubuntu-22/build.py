#!/usr/bin/env python3
import os.path
import sys

current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

# Docker image name basically
service_name = "ov-kit-ubuntu-22"

# Root - relative to config - for files' spec
root = "."

# Source files to set up in the build directory
files = [
    {"source": "data", "dest": "data", "files": ["startup.sh", "startup_nogpu.sh"]}
]


# Should return a string containing dockerfile.
def dockerfile(release=None, family=None, build=None):
    with open(f'{current_dir}/Dockerfile') as df:
        return df.read()
