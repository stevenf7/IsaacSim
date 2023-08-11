@echo off

:: NOTE: File attributes are not preserved when converting package on Windows.
call "%~dp0..\..\..\..\repo.bat" publish_assets_launcher_3 $@
if %errorlevel% neq 0 ( exit /b %errorlevel% )


