@echo off
set KIT_PATH=..\..\..\..\..\..\..\_build\windows-x86_64\release
set CARB_APP_PATH=%KIT_PATH%
call %KIT_PATH%\setup_python_env.bat
:Success
exit /b 0