@echo off

:: tests
call "%~dp0..\..\..\..\tools\test.bat" --suite internalnativepythontests --from-package --config release %*
if %errorlevel% neq 0 ( exit /b %errorlevel% )

