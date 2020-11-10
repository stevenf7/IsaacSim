@echo off

call "%~dp0..\..\..\package_launcher.bat"
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages/*.release.zip']


