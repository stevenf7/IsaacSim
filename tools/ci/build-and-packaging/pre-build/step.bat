@echo off

pushd "%~dp0..\..\..\.."

echo Generating build number
call tools\teamcity.bat --prepbuild
if %errorlevel% neq 0 (
    echo ##teamcity[buildStatus text='Error generating build number' status='ERROR']
    exit /b %errorlevel%
    )

echo Checking code formatting
call format_code.bat verify
if %errorlevel% neq 0 (
    echo ##teamcity[buildStatus text='Error formatting code' status='ERROR']
    exit /b %errorlevel%
    )

if defined GENERATE_CHANGES (
    echo Generating changes log
    call "tools\packman\python" "tools\buildscripts\generate_changes.py" %*
)
if %errorlevel% neq 0 (
    echo ##teamcity[buildStatus text='Error generating changelog' status='ERROR']
    exit /b %errorlevel%
)

:Success
exit /b 0