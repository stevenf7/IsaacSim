@echo off

if not exist PACKAGE-LICENSES (
    mkdir PACKAGE-LICENSES > nul 2>&1
)

call "%~dp0..\tools\packman\python" %~dp0repoman\licensing.py %*
