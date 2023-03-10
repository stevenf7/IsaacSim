#!/bin/bash

echo "edit this file and comment out the specific cache you want to clear"
echo "if you see permissions errors sudo might need to be added to the start of the specific rm -rf command"
echo "run this at your own risk :)"

# shader caches
#rm -rf ~/.cache/nvidia/GLCache
#rm -rf ~/.cache/shaders
#rm -rf ~/.cache/texturecache
#rm -rf ~/.cache/ov/Kit/
#rm -rf ~/.nv/ComputeCache/


# kit caches
#rm -rf ~/.local/share/ov/data/Kit/

# installed pip packages
#rm -rf ~/.local/lib/python3.7/site-packages

# launcher packages
#rm -rf ~/.local/share/ov/pkg/

# extension cache
#rm -rf ~/.cache/ov/exts/

# old logs:
#rm -rf ~/.nvidia-omniverse/logs/

# icon file
#rm -rf ~/.local/share/applications/IsaacSim.desktop

### system level caches that will take a while to re-download ###
# downloaded pip packages (deleting this will force all pip packages to be re-downloaded, can be slow)
# rm -rf ~/.cache/pip/http

# packman cache, this will force ALL packman dependencies to re-download which takes a very long time
# rm -rf $PM_PACKAGES_ROOT

# authentication cache, this will clear any saved logins
# mv ~/.nvidia-omniverse/config/omniverse.toml ~/.nvidia-omniverse/config/omniverse.toml.old