@echo off
setlocal

if defined TEAMCITY_VERSION (
    set "package=--from-package"
)

call "%~dp0..\..\..\test_runner.bat" --suite unittests --config release %package% -e ~[teamcityjob1] -e ~[teamcityjob2] -e ~[teamcityjob3] %*
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:Success
exit /b 0