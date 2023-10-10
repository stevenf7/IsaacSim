@echo off

if defined ISAACSIM_SKIP_POSTINSTALL (
    echo ISAACSIM_SKIP_POSTINSTALL was set. Post-install skipped.
    echo "ISAACSIM_SKIP_POSTINSTALL was set. Post-install skipped." >%~dp0omni.isaac.sim.post.install.log 2>&1
) else (

    echo "Isaac Sim Post-Installation Script" >%~dp0omni.isaac.sim.post.install.log 2>&1

    @REM Add symlink to Isaac Examples
    echo Creating extension_examples symlink...
    cmd /C "%~dp0omni.isaac.sim.create_junction.bat" >>%~dp0omni.isaac.sim.post.install.log 2>&1

    @REM Warm up shader cache
    @REM Run "setx /m ISAACSIM_SKIP_WARMUP Y" to skip warm up
    if not defined ISAACSIM_SKIP_WARMUP (
        echo start cmd /c "%~dp0omni.isaac.sim.post.install.run.bat"
        start cmd /c "%~dp0omni.isaac.sim.post.install.run.bat"
    ) else (
        echo ISAACSIM_SKIP_WARMUP was set. Warm up skipped.
        echo "ISAACSIM_SKIP_WARMUP was set. Warm up skipped." >>%~dp0omni.isaac.sim.post.install.log 2>&1
    )
)
