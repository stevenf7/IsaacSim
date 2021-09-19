#!/bin/bash
echo "edit this file and comment out the specific cache you want to clear"
echo "run this at your own risk :)"
# shader caches
# rm -rf ~/.cache/nvidia/GLCache
# rm -rf ~/.cache/ov/Kit/
# rm -rf ~/.nv/ComputeCache/

# kit caches
# rm -rf ~/.local/share/ov/data/Kit/

# installed pip packages
# rm -rf ~/.local/lib/python3.7/site-packages

# downloaded pip packages (deleting this will force all pip packages to be re-downloaded, can be slow)
# rm -rf ~/.cache/pip/http

# launcher packages
# rm -rf ~/.local/share/ov/pkg/

# extension cache
# rm -rf ~/.cache/ov/exts/