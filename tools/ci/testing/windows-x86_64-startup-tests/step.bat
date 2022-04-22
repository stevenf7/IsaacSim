@echo off

:: tests
call "%~dp0..\..\..\..\tools\test.bat" --suite postinstalltests --from-package --config release
call "%~dp0..\..\..\..\tools\test.bat" --suite startuptests --from-package --config release
call "%~dp0..\..\..\..\tools\test.bat" --suite launchertests --from-package --config release
if %errorlevel% neq 0 ( exit /b %errorlevel% )

