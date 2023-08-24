@echo off

echo "Isaac Sim Post-Installation Script"

@REM Add symlink to Isaac Examples
echo Creating extension_examples symlink...
cmd /C "%~dp0omni.isaac.sim.create_junction.bat" >%~dp0omni.isaac.sim.post.install.log 2>&1

@REM Install default Python packages
@REM @REM Run "setx ISAACSIM_SKIP_PIPINSTALL Y" to skip pip install step
@If Not Defined ISAACSIM_SKIP_PIPINSTALL (
    echo Installing Python packages... Please wait...
    call "%~dp0python.bat" -m pip install -r "%~dp0requirements.txt" >>%~dp0omni.isaac.sim.post.install.log 2>&1
    echo "Python packages installed." >>%~dp0omni.isaac.sim.post.install.log 2>&1
)

@REM @REM Warm up shader cache
@REM @REM Run "setx ISAACSIM_SKIP_WARMUP Y" to skip warm up
@If Not Defined ISAACSIM_SKIP_WARMUP (
    echo Warming up shader cache... Please wait...
    echo Close this window to skip.
    call "%~dp0omni.isaac.sim.warmup.bat" >>%~dp0omni.isaac.sim.post.install.log 2>&1
)

echo Isaac Sim Post-Installation Script completed!
echo "Isaac Sim Post-Installation Script completed!" >>%~dp0omni.isaac.sim.post.install.log 2>&1
