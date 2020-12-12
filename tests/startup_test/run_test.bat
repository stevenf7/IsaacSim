@echo off
setlocal

:: Modify TOOLS and/or PACKMAN to suit your case
:: Fill in the folder with the packman or/and ovat tools
set TOOLS=%~dp0\..\..\tools
set PACKMAN=%TOOLS%\packman

pushd %~dp0
call %PACKMAN%\python.bat %TOOLS%\ovat\run_test.py %*
popd
