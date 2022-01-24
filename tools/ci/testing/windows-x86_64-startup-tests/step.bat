@echo off

:: tests
@REM call "%~dp0..\..\..\..\repo.bat" test --config release --from-package
call "%~dp0..\..\..\..\tools\test.bat" --suite startuptests --from-package --config release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

