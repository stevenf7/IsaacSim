@echo off
setlocal

:: Use half of available CPU cores for the warmup not to take all the resources from user's PC during installation
set /a TASKING_THREAD_CNT = %NUMBER_OF_PROCESSORS% / 2
call "%~dp0kit\kit.exe"  "%%~dp0apps/omni.isaac.sim.kit" ^
    --no-window ^
    --/persistent/renderer/startupMessageDisplayed=true ^
    --ext-folder "%~dp0/exts" ^
    --ext-folder "%~dp0/apps" ^
    --/app/extensions/excluded/2='omni.kit.telemetry' ^
    --/app/settings/persistent=0 ^
    --/app/settings/loadUserConfig=0 ^
    --/structuredLog/enable=0 ^
    --/app/hangDetector/enabled=0 ^
    --/app/content/emptyStageOnStart=1 ^
    --/rtx/materialDb/syncLoads=1 ^
    --/omni.kit.plugin/syncUsdLoads=1 ^
    --/rtx/hydra/materialSyncLoads=1 ^
    --/app/asyncRendering=0 ^
    --/app/quitAfter=100 ^
    --/app/fastShutdown=true ^
    --/exts/omni.kit.registry.nucleus/registries/0/name=0 ^
    --/plugins/carb.tasking.plugin/threadCount=%TASKING_THREAD_CNT% ^
    %*
if %ERRORLEVEL% neq 0 (echo "Error warming up shader cache.") else (echo "Shader cache is warmed up.")

call "%~dp0python.bat" "%~dp0standalone_examples\api\omni.isaac.kit\hello_world.py"
if %ERRORLEVEL% neq 0 (echo "Error warming up python app shader cache.") else (echo "Python app shader cache is warmed up.")

:: Always succeed in case kit crashed or hanged
exit /b 0
