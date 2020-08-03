@echo off

pushd "%~dp0.."


if exist PACKAGE-LICENSES (
    del /Q /F PACKAGE-LICENSES\*.md > nul 2>&1
)
else (
    mkdir PACKAGE-LICENSES > nul 2>&1
)

copy "tools\internal-licenses" "PACKAGE-LICENSES" > nul 2>&1

call "%~dp0licensing.bat" gather -d "%cd%" -p "deps\isaac-sim.packman.xml" --platform "windows-x86_64" %LICENSING_OPTIONS% %*
if %errorlevel% neq 0 ( goto End )

call "%~dp0licensing.bat" gather -d "%cd%" -p "deps\kit-sdk.packman.xml" --platform "windows-x86_64" %LICENSING_OPTIONS% %*
if %errorlevel% neq 0 ( goto End )

if defined TEAMCITY_VERSION (
    del /q /s "PACKAGE-LICENSES\*readme*" > nul 2>&1
)

:End
popd
