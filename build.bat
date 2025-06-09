@echo off

:: Check EULA acceptance first
call "%~dp0tools\eula_check.bat"
if %errorlevel% neq 0 (
    echo Error: NVIDIA Software License Agreement and Product-Specific Terms for NVIDIA Omniverse must be accepted to proceed.
    exit /b 1
)

call "%~dp0repo" build %*
