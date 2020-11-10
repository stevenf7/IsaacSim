@echo off
setlocal

:: Modify this to suit your case
:: Fill in the folder with the packman and ovat tools
set TOOLS=%~dp0\..\..\tools

call %TOOLS%\packman\python.bat %TOOLS%\ovat\run_test.py %*
