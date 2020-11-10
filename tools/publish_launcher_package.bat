@echo off

call "%~dp0packman\python.bat" "%~dp0repoman\publish_launcher_package.py"
if errorlevel 1 (
    echo Error calling "%~dp0packman\python.bat" "%~dp0repoman\publish_launcher_package.py"
    exit /B
)
