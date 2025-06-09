@echo off
setlocal EnableDelayedExpansion

REM Get repository root (parent directory of script directory)
set REPO_ROOT=%~dp0..

REM Check if EULA has already been accepted in either current directory or repository root
if exist ".eula_accepted" (
    exit /b 0
) else if exist "%REPO_ROOT%\.eula_accepted" (
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
    type nul > "%REPO_ROOT%\.eula_accepted"
    exit /b 0
) else (
    exit /b 1
)
