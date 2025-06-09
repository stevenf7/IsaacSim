@echo off
setlocal EnableDelayedExpansion

REM Check if EULA has already been accepted in either current directory or script's directory
if exist ".eula_accepted" (
    exit /b 0
) else if exist "%~dp0.eula_accepted" (
    exit /b 0
)

echo === END USER LICENSE AGREEMENT ===
echo Building or using the software requires additional components licenced under other terms. These additional components include dependencies such as the Omniverse Kit SDK, as well as 3D models and textures.
echo.
echo License terms for these additional NVIDIA owned and licensed components can be found here:
echo.
echo https://www.nvidia.com/en-us/agreements/enterprise-software/isaac-sim-additional-software-and-materials-license/
echo.
echo ================================
echo.
set /p response="Do you accept the governing terms? (YES/NO): "

REM Check response
if /i "!response!"=="YES" (
    type nul > ".eula_accepted"
    type nul > "%~dp0.eula_accepted"
    exit /b 0
) else (
    exit /b 1
)
