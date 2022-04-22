@echo off
setlocal

@REM Warm up shader cache
echo "Warming up cache..."
call "%~dp0omni.isaac.sim.warmup.bat"

@REM Install default Python packages 
echo "Installing Python packages..."
call "%~dp0python.sh -m pip install -r %~dp0requirements.txt

echo "Isaac Sim post installation script completed!"