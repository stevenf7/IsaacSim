@echo off

:: build release
call "%~dp0..\..\..\..\build.bat" --release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: create launcher package
call "%~dp0..\..\..\package_launcher.bat"
if %errorlevel% neq 0 ( exit /b %errorlevel% )

:: publish artifacts to teamcity
echo ##teamcity[publishArtifacts '_build/packages/*.release.zip']


