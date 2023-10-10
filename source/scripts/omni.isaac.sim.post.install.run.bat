@echo off

echo "Isaac Sim Post-Installation Script"

@REM Warm up shader cache
@REM Run "setx ISAACSIM_SKIP_WARMUP Y" to skip warm up
if not defined ISAACSIM_SKIP_WARMUP (
    echo Warming up shader cache... Please wait...
    echo Close this window to skip.
    call "%~dp0omni.isaac.sim.warmup.bat" >>%~dp0omni.isaac.sim.post.install.log 2>&1
)

echo Isaac Sim Post-Installation Script completed!
echo "Isaac Sim Post-Installation Script completed!" >>%~dp0omni.isaac.sim.post.install.log 2>&1
