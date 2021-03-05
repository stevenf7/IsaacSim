@echo off

call "%~dp0..\..\..\..\repo.bat" bump_version
if %errorlevel% neq 0 ( exit /b %errorlevel% )


