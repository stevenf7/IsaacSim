@echo off
setlocal

:: Where are the tools located in relation to this script
set TOOLS=%~dp0..

echo Current directory: %cd%

echo Creating virtual environment and installing ovat-client
call %TOOLS%\packman\python.bat -m venv _venv
if %errorlevel% neq 0 goto :error

call .\_venv\Scripts\activate.bat
if %errorlevel% neq 0 goto :error

python -m pip install -U pip
pip config set --site global.extra-index-url https://pypi.perflab.nvidia.com/simple
pip install -U "ovat-client>=0.17.0"

echo Running tests
ovat jobs create-from-file -e teamcity
if %errorlevel% neq 0 goto :error
goto :end

:error
exit /b %errorlevel%

:end