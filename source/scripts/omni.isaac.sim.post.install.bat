@echo off
setlocal

@REM Add symlink to Isaac Examples
echo "Creating extension_examples symlink..."
cmd /C "%~dp0omni.isaac.sim.create_junction.bat"

@REM Warm up shader cache
echo "Warming up cache..."
call "%~dp0omni.isaac.sim.warmup.bat"
call "%~dp0python.sh %~dp0standalone_examples\api\omni.isaac.kit\hello_world.py

@REM Install default Python packages 
echo "Installing Python packages..."
call "%~dp0python.sh -m pip install -r %~dp0requirements.txt

echo "Isaac Sim post installation script completed!"