@echo off

:: tests
call "%~dp0..\..\..\..\tools\test.bat" --suite gympythontests --from-package --config release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

