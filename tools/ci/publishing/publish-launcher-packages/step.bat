@echo off

:: NOTE: File attributes are not preserved when converting package on Windows.
call "%~dp0..\..\..\..\repo.bat" publish_launcher $@
if %errorlevel% neq 0 ( exit /b %errorlevel% )


