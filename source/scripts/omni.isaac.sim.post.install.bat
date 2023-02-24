@echo off

@REM Add symlink to Isaac Examples
echo "Creating extension_examples symlink..."
cmd /C "%~dp0omni.isaac.sim.create_junction.bat"

@REM @REM Warm up shader cache
@REM @REM Run "setx ISAACSIM_SKIP_WARMUP Y" to skip warm up
@REM @If Not Defined ISAACSIM_SKIP_WARMUP (
@REM     echo "Warming up cache for main app..."
@REM     call "%~dp0omni.isaac.sim.warmup.bat"
@REM     echo "Warming up cache for python app..."
@REM     call "%~dp0python.bat" "%~dp0standalone_examples\api\omni.isaac.kit\hello_world.py"
@REM )

@REM Install default Python packages
echo "Installing Python packages..."
call "%~dp0python.bat" -m pip install -r "%~dp0requirements.txt"

echo "Isaac Sim post installation script completed!"
